import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT, ASCENDING
from pymongo.errors import DuplicateKeyError, OperationFailure, PyMongoError
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
        doc = await updates_collection.find_one({"title": normalized_title, "year": year})
        from utils import send_update
        if not doc:
            await updates_collection.insert_one({
                "title": normalized_title,
                "year": year
            })
            asyncio.create_task(send_update(title, year))
        else:
            msg_id = doc.get("message_id")
            asyncio.create_task(send_update(title, year, edit_message_id=msg_id))
    except Exception as e:
        logger.error(f"Error in trigger_update_if_new: {e}")


async def save_file(media):
    file_id = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name))
    file_caption = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.caption))

    try:
        from database.users_chats_db import db as users_db
        bad_words = await users_db.get_bad_words()
        for word in bad_words:
            if word:
                file_name = re.sub(rf'(?i){re.escape(word)}', ' ', file_name)
        file_name = re.sub(r'\s+', ' ', file_name).strip()
    except Exception as ex:
        logger.error(f"Error stripping bad words in save_file: {ex}")
    
    document = {
        '_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': file_caption
    }
    
    data = PTN.parse(file_name)
    title = data.get('title')
    year = data.get('year')
    if not title:
        cleaned_title = re.sub(r'(?i)(s\d+|season\s*\d+|e\d+|ep\d+|episode\s*\d+|\d+x\d+).*$', '', file_name)
        cleaned_title = re.sub(r'[._-]', ' ', cleaned_title).strip()
        title = cleaned_title if cleaned_title else file_name

    if SECOND_FILES_DATABASE_URL and second_collection is not None:
        if await second_collection.find_one({'_id': file_id}):
            logger.warning(f'Already Saved in 2nd db - {file_name}')
            return 'dup'
    
    try:
        await collection.insert_one(document)
        logger.info(f'Saved - {file_name}')
        
        await trigger_update_if_new(title, year)
        return 'suc'
        
    except DuplicateKeyError:
        logger.warning(f'Already Saved - {file_name}')
        return 'dup'
        
    except (OperationFailure, PyMongoError) as e:
        if SECOND_FILES_DATABASE_URL and second_collection is not None:
            try:
                await second_collection.insert_one(document)
                logger.info(f'Saved to 2nd db - {file_name}')
                
                await trigger_update_if_new(title, year)
                return 'suc'
                
            except DuplicateKeyError:
                logger.warning(f'Already Saved in 2nd db - {file_name}')
                return 'dup'
            except Exception as ex:
                logger.error(f'Failed to save to 2nd db: {ex}')
                return 'err'
        else:
            logger.error(f'Your FILES_DATABASE_URL is full or failed: {e}')
            return 'err'


async def get_search_results(query):
    query = str(query).strip()
    if not query:
        recent_limit = 100  # default limit for fetching recently added files
        results = []
        seen_ids = set()
        
        cursor1 = collection.find({}).sort("_id", -1).limit(recent_limit)
        docs1 = await cursor1.to_list(length=recent_limit)
        for doc in docs1:
            if doc['_id'] not in seen_ids:
                seen_ids.add(doc['_id'])
                results.append(doc)

        if SECOND_FILES_DATABASE_URL and second_collection is not None and len(results) < recent_limit:
            remaining_limit = recent_limit - len(results)
            cursor2 = second_collection.find({}).sort("_id", -1).limit(remaining_limit)
            docs2 = await cursor2.to_list(length=remaining_limit)
            for doc in docs2:
                if doc['_id'] not in seen_ids:
                    seen_ids.add(doc['_id'])
                    results.append(doc)

        return results

    import re
    raw_query = str(query).strip()
    cleaned_query = re.sub(r"@\w+|[^\w\s]|_", " ", raw_query)
    cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()

    words = cleaned_query.split()
    if not words:
        return []

    regex_patterns = []
    for w in words:
        se_match = re.match(r"^(?:s|season)?0*(\d{1,2})(?:e|ep|episode)?0*(\d{1,2})$", w, re.IGNORECASE)
        s_match = re.match(r"^(?:s|season)0*(\d{1,2})$", w, re.IGNORECASE)
        e_match = re.match(r"^(?:e|ep|episode)0*(\d{1,2})$", w, re.IGNORECASE)

        if se_match and (w.lower().startswith("s") or "e" in w.lower()):
            s_num, e_num = se_match.groups()
            pattern = rf"(?:s0*{s_num}[\s\.\-_]*e0*{e_num}|s0*{s_num}|e0*{e_num}|\b0*{s_num}x0*{e_num}\b|{re.escape(w)})"
            regex_patterns.append(pattern)
        elif s_match and not w.isdigit():
            s_num = s_match.group(1)
            pattern = rf"(?:s0*{s_num}\b|season[\s\.\-_]*0*{s_num}\b|{re.escape(w)})"
            regex_patterns.append(pattern)
        elif e_match and not w.isdigit():
            e_num = e_match.group(1)
            pattern = rf"(?:e0*{e_num}\b|ep0*{e_num}\b|episode[\s\.\-_]*0*{e_num}\b|{re.escape(w)})"
            regex_patterns.append(pattern)
        else:
            regex_patterns.append(re.escape(w))

    db_query_list = [{"file_name": {"$regex": pat, "$options": "i"}} for pat in regex_patterns]
    search_filter = {"$or": [{"$and": db_query_list}]}
    
    if USE_CAPTION_FILTER:
        caption_query_list = [{"caption": {"$regex": pat, "$options": "i"}} for pat in regex_patterns]
        search_filter["$or"].append({"$and": caption_query_list})

    results = []
    seen_ids = set()
    
    cursor1 = collection.find(search_filter)
    docs1 = await cursor1.to_list(length=None) 
    for doc in docs1:
        if doc['_id'] not in seen_ids:
            seen_ids.add(doc['_id'])
            results.append(doc)

    if SECOND_FILES_DATABASE_URL and second_collection is not None:
        cursor2 = second_collection.find(search_filter)
        docs2 = await cursor2.to_list(length=None)
        for doc in docs2:
            if doc['_id'] not in seen_ids:
                seen_ids.add(doc['_id'])
                results.append(doc)

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


async def remove_bad_words_from_db(words):
    if not words:
        return 0
    updated_count = 0
    for word in words:
        w_str = str(word).strip()
        if not w_str:
            continue
        pattern = re.compile(re.escape(w_str), flags=re.IGNORECASE)
        filter_query = {'file_name': pattern}

        cursor1 = collection.find(filter_query)
        async for doc in cursor1:
            new_title = re.sub(pattern, '', doc['file_name'])
            new_title = re.sub(r'\s+', ' ', new_title)
            new_title = re.sub(r'\s+\.', '.', new_title).strip()
            if new_title != doc['file_name']:
                await collection.update_one({'_id': doc['_id']}, {'$set': {'file_name': new_title}})
                updated_count += 1

        if SECOND_FILES_DATABASE_URL and second_collection is not None:
            cursor2 = second_collection.find(filter_query)
            async for doc in cursor2:
                new_title = re.sub(pattern, '', doc['file_name'])
                new_title = re.sub(r'\s+', ' ', new_title)
                new_title = re.sub(r'\s+\.', '.', new_title).strip()
                if new_title != doc['file_name']:
                    await second_collection.update_one({'_id': doc['_id']}, {'$set': {'file_name': new_title}})
                    updated_count += 1

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

    return updated_count


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

