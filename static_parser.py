
import sys, os, socket, time
from scraper.static import StaticScraper
from logs import init_log

#########################################
####                                 ####
####                                 ####
####                                 ####
#########################################

# SYS ARGUMENTS
try:
    if sys.argv != ['']:

        argv = sys.argv

        NUM_PROCESS = int(argv[1])
        LIMIT = int(argv[2])
        

        try:
            LOOP = bool(int(argv[3]))
            FOR_ARTICLE = bool(int(argv[4]))
        except:
            pass

    else:
        NUM_PROCESS = 1
        LIMIT = os.cpu_count() - 1
        FOR_ARTICLE = False

except IndexError:
    NUM_PROCESS = 1
    LIMIT = 1
    LOOP = False
    FOR_ARTICLE = False

log = init_log('StaticScraperMain')

if __name__ == '__main__':

    # CHECK IF PROCESS IS ALREADY RUNNING
    PID = str(os.getpid())
    PID_FILE = f"{str(socket.gethostname())}.pid"
    try:
        PID_FILE_PROCESS = int(open(PID_FILE, 'r').readlines[0])
    except FileNotFoundError:
        PID_FILE_PROCESS = int(open(PID_FILE, 'w').readlines[0])

    if all([PID_FILE_PROCESS is not None, (os.path.isfile(PID_FILE) and StaticScraper.is_running(PID_FILE_PROCESS))]):
        log.debug(f"Process {PID} already running")
        sys.exit()
    else:
        with open(PID_FILE, 'w') as f:
            f.write(PID)

    # MAIN LOOP
    while True:
        # CHECK IF NEED TO END SCRAPER
        if StaticScraper.endtime(for_article=FOR_ARTICLE): break

        # CHECK FOR UNPROCESSED LINKS
        StaticScraper.check_unprocessed_links(for_article=FOR_ARTICLE)

        # INIT
        start = time.time()
        date = datetime.datetime.now()
        date_format = date.strftime("%Y-%m-%d-%H%M%S")
        log.info(f"Started scraper at {date_format}")

        # CHECK FOR QUEUED ARTICLES. SLEEP IF NONE FOUND
        if StaticScraper.check_queued(FOR_ARTICLE) == 0:
            log.info("No article to scrape. Sleeping...")
            if not StaticScraper.endtime(FOR_ARTICLE):
                break
            else:
                continue
         
        # GET LINKS TO PROCESS
        articles = StaticScraper.get_queued_links(LIMIT * NUM_PROCESS, for_article=FOR_ARTICLE)

        # CALL MAIN PROCESS
        StaticScraper.multiprocess(articles, NUM_PROCESS, StaticScraper.parse_article, for_article=FOR_ARTICLE)


    os.unlink(pidfile)
                


