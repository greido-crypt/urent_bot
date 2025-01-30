import asyncio

from db.repository import presents_repository


async def main():
    with open('prizes.txt', 'r') as f:
        prizes = f.read().splitlines()

    await presents_repository.addPresents()

if __name__ == '__main__':
    asyncio.run(main())