from utilities.logger import Logger
from utilities.embedding import create_embedding_bge
from utilities.dbtool import DBHandler
import sys
import faiss

# mode = sys.argv[1] if len(sys.argv) > 1 else "kb"
# LOG.debug("Mode selected:", mode)
mode = 'req'
LOG = Logger(name='local', debug=True).logger

def validate(db_handler, index_file, db_name, invalid_vector_id=99999):
    index = faiss.read_index(index_file)
    query = f"SELECT vector_id FROM {db_name} WHERE vector_id is not NULL and vector_id != {invalid_vector_id}"
    db_handler.execute_query(query)
    res = db_handler.fetchall()
    if len(res) - index.ntotal == 0:
        debug_str = 'PASS'
    else:
        debug_str = 'FAIL'
    LOG.debug(f'{debug_str} length check. Length of {db_name} db is {len(res)}, length of FAISS is {index.ntotal}')

    query = f"SELECT vector_id FROM {db_name}"
    db_handler.execute_query(query)
    t_res = db_handler.fetchall()
    if len(res) - len(t_res) == 0:
        debug_str = 'PASS'
    else:
        debug_str = 'FAIL'
    LOG.debug(f'{debug_str} invalid vector_id check. Totally {len(t_res)} vector_id, valid {len(res)}')

    query = f"SELECT min(vector_id), max(vector_id) FROM {db_name}"
    db_handler.execute_query(query)
    t_res = db_handler.fetchone()
    minv, maxv = t_res
    if (minv==0 or minv==-1) and maxv==len(res)-1:
        debug_str = 'PASS'     
    else:
        debug_str = 'FAIL'
    LOG.debug(f'{debug_str} vector_id range check. Min value is {minv}, max is {maxv}')

    vlist = []
    for item in res:
        vlist.append(item[0])
    vset = set(vlist)    
    if len(vset) == len(vlist):
        debug_str = 'PASS'
    else:
        debug_str = 'FAIL'   
    LOG.debug(f'{debug_str} vector_id duplication check. Totally {len(vlist)} vector_id, {len(vset)} distinct')

if mode == 'kb':
    db_handler = DBHandler('knowledgebase')
    db_name = 'knowledgebase'
    index_file = 'vecdb/bge_ms_index_summary.faiss'
    validate(db_handler, index_file, db_name)

    db_name = 'textpoints_1204'
    index_file = 'vecdb/bge_ms_index_textpoints.faiss'
    validate(db_handler, index_file, db_name)    
elif mode == 'req':
    db_handler = DBHandler('requirements')
    db_name = 'stories'
    index_file = 'vecdb/story_new.faiss'
    validate(db_handler, index_file, db_name, invalid_vector_id=-1)

    db_name = 'stories_bp'
    index_file = 'vecdb/bp_story_new.faiss'
    validate(db_handler, index_file, db_name)
elif mode == 'code':
    db_handler = DBHandler('codebase')
    db_name = 'method_info'
    index_file = 'vecdb/method_embedding.index'
    validate(db_handler, index_file, db_name)
else:
    LOG.error(f'{mode} is incorrect')
