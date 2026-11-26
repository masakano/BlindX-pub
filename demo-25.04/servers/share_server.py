#!/usr/bin/env python3
#
# chat server

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#
import blindx.misc as misc
import asyncio
import hmac
import websockets
import logging

misc.set_logger(__file__)
logger = logging.getLogger(__name__)
connected_clients = set()
connected_names = {}
lines = []
share_server_key = None

available_names = [
    'Alice', 'Bob', 'Charol', 'Charile', 'Dave', 'Eve', 'Ellen', 'Frank', 'Isac', 'IVan', 
    'Justin', 'Marvin', 'Matilda', 'Oscar', 'Peggy', 'Steve', 'Trent', 'Trudy', 'Walter', 'Zoe' 
]

def report():
    print('line:')
    for lineno, line in enumerate(lines):
        replaced_line = line.replace('\n', '\\n')
        print(f"{lineno} : {replace_line}")


async def send_all_async(websocket, message):
    for client in connected_clients:
        if client != websocket:
            await client.send(message)

def load_share_server_key():
    key = misc.load_args_from_file('assets/config.txt').get('share_server_key')
    return str(key) if key is not None else None

async def verify_async(websocket):
    # share_server_key が設定されていれば、サブプロトコルで渡されたキーと照合する
    if not share_server_key:
        return True
    subprotocol = websocket.subprotocol or ''
    if hmac.compare_digest(subprotocol, share_server_key):
        return True
    logger.warning('unauthorized client')
    await websocket.close(code=4001, reason='unauthorized')
    return False

async def handle_client(websocket):
    global lines
    if not await verify_async(websocket):
        return

    if not websocket in connected_clients:
        connected_clients.add(websocket)
        name = available_names.pop(0)
        available_names.append(name)
        connected_names[websocket] = name

    try:
        async for message in websocket:
            # print('\t' + message.replace('\n', '\\n'))
            if message == 'clear:':
                logger.info('recv clear')
                lines = []
                await send_all_async(websocket, 'clear:')

            elif message == 'reload:':
                logger.info('recv reload')
                name_message = 'name' + ':' + connected_names[websocket]

                for key, value in connected_names.items():
                    if key != websocket: 
                        name_message += ':' + value

                await websocket.send(name_message)
                for line in lines:
                    await websocket.send(line)
            else:
                try:
                    lineno = int(message.split(':', 1)[0])
                    lines.extend(['']  * (lineno + 1 - len(lines)))
                    lines[lineno] = message
                    await send_all_async(websocket, message)
                except Exception as e:
                    logger.warning(f'invalid message message={message} except={e}')
                # report()    

    except websockets.ConnectionClosed:
        logger.info('client disconnected')
    finally:
        logger.info('client removed')
        name = connected_names[websocket]
        connected_clients.remove(websocket)
        del connected_names[websocket]

async def main():
    global share_server_key
    logger.info('start')
    share_server_key = load_share_server_key()
    if share_server_key:
        subprotocols = [share_server_key]
    else:
        subprotocols = None
        logger.warning('share_server_key is not set. clients are not authenticated.')

    async with websockets.serve(handle_client, "localhost", 6790, subprotocols=subprotocols):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
