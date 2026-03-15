#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import torch
import traceback
import socket
import json
from scene.cameras import MiniCam

host = "127.0.0.1"
port = 6009

conn = None
addr = None

listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def disconnect():
    global conn
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    conn = None

def init(wish_host, wish_port):
    global host, port, listener
    host = wish_host
    port = wish_port
    listener.bind((host, port))
    listener.listen()
    listener.settimeout(0)

def try_connect():
    global conn, addr, listener
    try:
        conn, addr = listener.accept()
        print(f"\nConnected by {addr}")
        conn.settimeout(None)
    except (BlockingIOError, socket.timeout):
        # No pending GUI client yet; train/pretrain call try_connect() each iteration.
        pass
    except Exception as inst:
        disconnect()
        print(f"\nNetwork GUI connection failed: {inst}")

def _recv_exact(num_bytes):
    global conn
    data = bytearray()
    while len(data) < num_bytes:
        chunk = conn.recv(num_bytes - len(data))
        if not chunk:
            raise ConnectionError("Socket connection closed while receiving data.")
        data.extend(chunk)
    return bytes(data)
             
def read():
    global conn
    messageLength = _recv_exact(4)
    messageLength = int.from_bytes(messageLength, 'little')
    message = _recv_exact(messageLength)
    return json.loads(message.decode("utf-8"))

def send(message_bytes, verify):
    global conn
    if conn is None:
        return
    try:
        if message_bytes is not None:
            conn.sendall(message_bytes)
        conn.sendall(len(verify).to_bytes(4, 'little'))
        conn.sendall(bytes(verify, 'ascii'))
    except Exception:
        disconnect()
        raise

def receive():
    message = read()

    width = message["resolution_x"]
    height = message["resolution_y"]

    if width != 0 and height != 0:
        try:
            do_training = bool(message["train"])
            fovy = message["fov_y"]
            fovx = message["fov_x"]
            znear = message["z_near"]
            zfar = message["z_far"]
            do_shs_python = bool(message["shs_python"])
            do_rot_scale_python = bool(message["rot_scale_python"])
            keep_alive = bool(message["keep_alive"])
            scaling_modifier = message["scaling_modifier"]
            world_view_transform = torch.reshape(torch.tensor(message["view_matrix"]), (4, 4)).cuda()
            world_view_transform[:,1] = -world_view_transform[:,1]
            world_view_transform[:,2] = -world_view_transform[:,2]
            full_proj_transform = torch.reshape(torch.tensor(message["view_projection_matrix"]), (4, 4)).cuda()
            full_proj_transform[:,1] = -full_proj_transform[:,1]
            custom_cam = MiniCam(width, height, fovy, fovx, znear, zfar, world_view_transform, full_proj_transform)
        except Exception as e:
            print("")
            traceback.print_exc()
            disconnect()
            raise e
        return custom_cam, do_training, do_shs_python, do_rot_scale_python, keep_alive, scaling_modifier
    else:
        return None, None, None, None, None, None
