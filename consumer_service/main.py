from fastapi import FastAPI, HTTPException
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import asyncio
import uvicorn
import json
import logging

from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

loop = asyncio.get_event_loop()
consumer = AIOKafkaConsumer(
    'request_topic',
    loop=loop,
    bootstrap_servers='kafka:9092',
    group_id="request_group"
)
producer = AIOKafkaProducer(loop=loop, bootstrap_servers='kafka:9092')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

items = []

@app.on_event("startup")
async def startup_event():
    retries = 5
    for i in range(retries):
        try:
            await consumer.start()
            await producer.start()
            break
        except Exception as e:
            logging.error(f"Failed to start consumer/producer, retrying {i+1}/{retries}...")
            await asyncio.sleep(5)
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to Kafka after several retries")

    asyncio.create_task(consume_messages())

@app.on_event("shutdown")
async def shutdown_event():
    await consumer.stop()
    await producer.stop()

async def consume_messages():
    async for msg in consumer:
        item = json.loads(msg.value.decode('utf-8'))
        items.append(item)
        response = {"status": "Item stored", "item": item}
        await producer.send_and_wait("response_topic", json.dumps(response).encode('utf-8'))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)