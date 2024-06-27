from fastapi import FastAPI, HTTPException
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import uvicorn
import json
import logging

from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

loop = asyncio.get_event_loop()
producer = AIOKafkaProducer(loop=loop, bootstrap_servers='kafka:9092')
consumer = AIOKafkaConsumer(
    'response_topic',
    loop=loop,
    bootstrap_servers='kafka:9092',
    group_id="response_group"
)

# add cors

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    retries = 5
    for i in range(retries):
        try:
            await producer.start()
            await consumer.start()
            break
        except Exception as e:
            logging.error(f"Failed to start producer/consumer, retrying {i + 1}/{retries}...")
            await asyncio.sleep(5)
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to Kafka after several retries")


@app.on_event("shutdown")
async def shutdown_event():
    await producer.stop()
    await consumer.stop()


@app.post("/items/")
async def get_items(item: dict):
    try:
        await producer.send_and_wait("request_topic", json.dumps(item).encode('utf-8'))

        # Wait for the response from the consumer
        msg = await consumer.getone()
        response = json.loads(msg.value.decode('utf-8'))

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)