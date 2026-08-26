from multiprocessing import Process, JoinableQueue
from parsers.cybewnews import CyberNewsConsumer, CyberNewsProducer
from config import SOURCES

NUM_CONSUMERS = 4  # Number of parallel article-parsing processes

def producer_worker(base_url, language_code, queue):
    """Task for collecting links."""
    producer = CyberNewsProducer(base_url, language_code, queue)
    producer.start()

def consumer_worker(queue):
    """Task for parsing the articles themselves."""
    consumer = CyberNewsConsumer()
    while True:
        task = queue.get()
        if task is None:
            queue.task_done()
            break
            
        url, language_code = task
        try:
            consumer.process_article(url, language_code)
        except Exception as e:
            print(f"Error processing {url}: {e}")
        finally:
            queue.task_done()

def main():
    # Queue for passing links from Producers to Consumers
    url_queue = JoinableQueue()

    # 1. Start Consumers (Parsers)
    consumers = []
    for _ in range(NUM_CONSUMERS):
        p = Process(target=consumer_worker, args=(url_queue,))
        p.start()
        consumers.append(p)

    # 2. Start Producers (Link collectors)
    producers = []
    for source in SOURCES:
        for link in source["urls"]:
            p = Process(target=producer_worker, args=(link, source["language_code"], url_queue))
            p.start()
            producers.append(p)

    # 3. Wait for all Producers to finish
    for p in producers:
        p.join()

    # 4. Wait until Consumers process all items in the queue
    url_queue.join()

    for _ in range(NUM_CONSUMERS):
        url_queue.put(None)
        
    for p in consumers:
        p.join()

    print("Парсинг успешно завершен.")

if __name__ == "__main__":
    main()