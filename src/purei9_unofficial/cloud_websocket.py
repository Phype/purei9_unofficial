import websocket
import time
import json

def on_message(ws, message):
    print("recv" + message)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    pass
    """
    
    
    Request<int>("Hello", value);
    
    
    await Send(new Message
		{
			Type = MessageType.Request,
			Body = body,
			Command = command
		});
        """
    
    ws.send(json.dumps({
        "Type": 1, # 1 Requst, 2 Response, 3 Event
        "Command": "Hello",
        "Body": 1
    }))
    
    ws.send(json.dumps({
        "Type": 1, # 1 Requst, 2 Response, 3 Event
        "Command": "AppUpdate",
        "Body": {
            "CleaningCommand": 3,
        }
    }))

if __name__ == "__main__":
    
    headers = {
        "Email": "p.jeitner@posteo.de",
        "AccountPassword": "mN5TZIDTWlcWge3iZxy9hC0JmckCZU/1/+c0tIMJlQ0=",
        "RobotId": "900277283814002391100106",
        #"DeviceId": "efebfbc2-7b46-4f78-80d0-098b755900e5",
    }

    websocket.enableTrace(True)
    ws = websocket.WebSocket()

    ws.connect("wss://mobile.rvccloud.electrolux.com/api/v1/websocket/AppUser", header = headers)
    ws.send(json.dumps({
            "Type": 1, # 1 Requst, 2 Response, 3 Event
            "Command": "AppUpdate",
            "Body": {
                "CleaningCommand": 3,
            }
    }))
    print(ws.recv())
    ws.close()
    
    """
    websocket.enableTrace(True)
    ws = websocket.WebSocket("wss://mobile.rvccloud.electrolux.com/api/v1/websocket/AppUser",
                              on_open = on_open,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close,
                              header = headers)
    

    ws.run_forever()
    """
