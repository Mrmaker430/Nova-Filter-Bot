import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure
from info import USE_CAPTION_FILTER, FILES_DATABASE_URL, SECOND_FILES_DATABASE_URL, DATABASE_NAME, COLLECTION_NAME, MAX_BTN, DATA_DATABASE_URL
import PTN, asyncio
from database.users_chats_db import data_db

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(FILES_DATABASE_URL)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

second_client = None
second_db = None
second_collection = None

if SECOND_FILES_DATABASE_URL:
    second_client = AsyncIOMotorClient(SECOND_FILES_DATABASE_URL)
    second_db = second_client[DATABASE_NAME]
    second_collection = second_db[COLLECTION_NAME]

updates_collection = data_db['notified_media']

async def setup_database():
    try:
        await updates_collection.create_index(
            [("title", ASCENDING), ("year", ASCENDING)],
            unique=True,
            name="title_year_unique"
        )
        logger.info("DATA_DATABASE_URL update indexes created/verified.")
    except OperationFailure as e:
        if e.code == 85:  # IndexOptionsConflict
            logger.warning("DATA_DATABASE_URL update index conflict detected. Dropping old indexes and recreating...")
            await updates_collection.drop_indexes() 
            await updates_collection.create_index(
                [("title", ASCENDING), ("year", ASCENDING)],
                unique=True,
                name="title_year_unique"
            )
            logger.info("DATA_DATABASE_URL update indexes recreated successfully.")
        else:
            logger.warning(f"Failed to create DATA_DATABASE_URL index: {e}")

    try:
        await collection.create_index([("file_name", TEXT), ("caption", TEXT)], name="file_name_caption_text")
        logger.info("FILES_DATABASE_URL indexes created/verified.")
    except OperationFailure as e:
        if e.code == 85:  # IndexOptionsConflict
            logger.warning("FILES_DATABASE_URL index conflict detected. Dropping old text indexes and recreating...")
            await collection.drop_indexes() 
            await collection.create_index([("file_name", TEXT), ("caption", TEXT)], name="file_name_caption_text")
            logger.info("FILES_DATABASE_URL indexes recreated successfully.")
        elif 'quota' in str(e).lower():
            if not SECOND_FILES_DATABASE_URL:
                logger.error('Your FILES_DATABASE_URL quota is full, add SECOND_FILES_DATABASE_URL. (Bot will still work for searching)')
            else:
                logger.info('FILES_DATABASE_URL quota is full, relying on SECOND_FILES_DATABASE_URL')
        else:
            logger.warning(f"Failed to create FILES_DATABASE_URL index: {e}")

    if SECOND_FILES_DATABASE_URL and second_collection is not None:
        try:
            await second_collection.create_index([("file_name", TEXT), ("caption", TEXT)], name="file_name_caption_text")
            logger.info("SECOND_FILES_DATABASE_URL indexes created/verified.")
        except OperationFailure as e:
            if e.code == 85:
                logger.warning("SECOND_FILES_DATABASE_URL index conflict detected. Dropping old text indexes and recreating...")
                await second_collection.drop_indexes()
                await second_collection.create_index([("file_name", TEXT), ("caption", TEXT)], name="file_name_caption_text")
                logger.info("SECOND_FILES_DATABASE_URL indexes recreated successfully.")
            else:
                logger.warning(f"Failed to create SECOND_FILES_DATABASE_URL index: {e}")


async def second_db_count_documents():
    if second_collection is None:
        return 0
    return await second_collection.count_documents({})

async def db_count_documents():
    return await collection.count_documents({})


async def trigger_update_if_new(title, year):
    if not title:
        return
    from database.users_chats_db import db as users_db
    if not await users_db.get_movie_update_status():
        return
    normalized_title = str(title).strip().lower()
    try:
        await updates_collection.insert_one({
            "title": normalized_title, 
            "year": year
        })
        from utils import send_update
        asyncio.create_task(send_update(title, year))
    except DuplicateKeyError:
        pass


async def save_file(media):
    file_id = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name))
    file_caption = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.caption))
    
    document = {
        '_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': file_caption
    }
    
    data = PTN.parse(file_name)
    title = data.get('title')
    year = data.get('year')
    
    try:
        await collection.insert_one(document)
        logger.info(f'Saved - {file_name}')
        
        await trigger_update_if_new(title, year)
        return 'suc'
        
    except DuplicateKeyError:
        logger.warning(f'Already Saved - {file_name}')
        return 'dup'
        
    except OperationFailure:
        if SECOND_FILES_DATABASE_URL and second_collection is not None:
            try:
                await second_collection.insert_one(document)
                logger.info(f'Saved to 2nd db - {file_name}')
                
                await trigger_update_if_new(title, year)
                return 'suc'
                
            except DuplicateKeyError:
                logger.warning(f'Already Saved in 2nd db - {file_name}')
                return 'dup'
        else:
            logger.error('Your FILES_DATABASE_URL is full, add SECOND_FILES_DATABASE_URL')
            return 'err'


async def get_search_results(query):
    query = str(query).strip()
    if not query:
        recent_limit = 100  # default limit for fetching recently added files
        results = []
        
        cursor1 = collection.find({}).sort("_id", -1).limit(recent_limit)
        docs1 = await cursor1.to_list(length=recent_limit)
        results.extend(docs1)

        if SECOND_FILES_DATABASE_URL and second_collection is not None and len(results) < recent_limit:
            remaining_limit = recent_limit - len(results)
            cursor2 = second_collection.find({}).sort("_id", -1).limit(remaining_limit)
            docs2 = await cursor2.to_list(length=remaining_limit)
            results.extend(docs2)

        return results

    import PTN
    import re
    parsed = PTN.parse(query)
    title = parsed.get("title", query).strip()

    title_words = [re.escape(word) for word in title.split()]
    raw_pattern = r'[\s\.\+\-_]+'.join(title_words) if len(title_words) > 1 else r'\b' + re.escape(title) + r'\b'
    
    and_conditions = [{"$regex": raw_pattern, "$options": "i"}]
    
    if parsed.get("year"):
        and_conditions.append({"$regex": rf"\b{parsed['year']}\b", "$options": "i"})
    if parsed.get("season"):
        and_conditions.append({"$regex": rf"\b(s|season)[\s\.\-_]*0?{parsed['season']}\b", "$options": "i"})
    if parsed.get("episode"):
        and_conditions.append({"$regex": rf"\b(e|episode|ep)[\s\.\-_]*0?{parsed['episode']}\b", "$options": "i"})
    if parsed.get("language"):
        and_conditions.append({"$regex": rf"\b{parsed['language']}\b", "$options": "i"})
    if parsed.get("resolution"):
        and_conditions.append({"$regex": rf"\b{parsed['resolution']}\b", "$options": "i"})
    if parsed.get("quality"):
        and_conditions.append({"$regex": rf"\b{parsed['quality']}\b", "$options": "i"})
    if parsed.get("codec"):
        and_conditions.append({"$regex": rf"\b{parsed['codec']}\b", "$options": "i"})
    
    db_query_list = [{"file_name": cond} for cond in and_conditions]
    search_filter = {"$or": [{"$and": db_query_list}]}
    
    if USE_CAPTION_FILTER:
        caption_query_list = [{"caption": cond} for cond in and_conditions]
        search_filter["$or"].append({"$and": caption_query_list})

    results = []
    
    cursor1 = collection.find(search_filter)
    docs1 = await cursor1.to_list(length=None) 
    results.extend(docs1)

    if SECOND_FILES_DATABASE_URL and second_collection is not None:
        cursor2 = second_collection.find(search_filter)
        docs2 = await cursor2.to_list(length=None)
        results.extend(docs2)

    return results


async def delete_files(query):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        regex = query
        
    filter_query = {'file_name': regex}
    
    result1 = await collection.delete_many(filter_query)
    total_deleted = result1.deleted_count
    
    if SECOND_FILES_DATABASE_URL and second_collection is not None:
        result2 = await second_collection.delete_many(filter_query)
        total_deleted += result2.deleted_count

    try:
        from utils import temp
        temp.QUERY_CACHE.clear()
    except Exception:
        pass
    try:
        from plugins.pm_filter import QUERY_CACHE
        QUERY_CACHE.clear()
    except Exception:
        pass

    return total_deleted


async def delete_all_files():
    result1 = await collection.delete_many({})
    total_deleted = result1.deleted_count

    if SECOND_FILES_DATABASE_URL and second_collection is not None:
        result2 = await second_collection.delete_many({})
        total_deleted += result2.deleted_count

    try:
        from utils import temp
        temp.QUERY_CACHE.clear()
    except Exception:
        pass
    try:
        from plugins.pm_filter import QUERY_CACHE
        QUERY_CACHE.clear()
    except Exception:
        pass
    
    return total_deleted


async def get_file_details(query):
    file_details = await collection.find_one({'_id': query})
    if not file_details and SECOND_FILES_DATABASE_URL and second_collection is not None:
        file_details = await second_collection.find_one({'_id': query})
    return file_details


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    return file_id

