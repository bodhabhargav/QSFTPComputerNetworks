import asyncio
import os
import sys
from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import HandshakeCompleted, StreamDataReceived
import ssl

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class QSFTPClientProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connected = asyncio.Event()
        self.data_received = asyncio.Event()
        self.received_data = None

    def quic_event_received(self, event):
        if isinstance(event, HandshakeCompleted):
            self.connected.set()
        elif isinstance(event, StreamDataReceived):
            self.received_data = event.data
            self.data_received.set()


async def send_data():
    configuration = QuicConfiguration(is_client=True)
    configuration.verify_mode = ssl.CERT_NONE  # Trust self-signed certificates

    file_path = input("Enter the file path to send: ").strip()
    if not os.path.isfile(file_path):
        print("Error: File not found")
        return
    file_name = os.path.basename(file_path)

    async with connect('localhost', 5000, configuration=configuration, create_protocol=QSFTPClientProtocol) as protocol:
        await protocol.connected.wait()  # Wait for handshake to complete

        quic_connection = protocol._quic

        # Send connection request
        control_stream_id = quic_connection.get_next_available_stream_id()
        quic_connection.send_stream_data(control_stream_id, f"CONN_REQUEST:{file_name}".encode(), end_stream=True)
        await protocol.data_received.wait()
        response = protocol.received_data.decode()
        print("Server response:", response)

        if response.startswith("ERROR"):
            print("Error:", response)
            return

        # Check if the connection was acknowledged
        if response == "CONN_ACK":
            # Send file data on a new stream
            file_stream_id = quic_connection.get_next_available_stream_id()
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(1024):
                        quic_connection.send_stream_data(file_stream_id, chunk)
                quic_connection.send_stream_data(file_stream_id, b"", end_stream=True)
            except FileNotFoundError:
                print("Error: File Not Found")
                error_stream_id = quic_connection.get_next_available_stream_id()
                quic_connection.send_stream_data(error_stream_id, b"ERROR:File Not Found", end_stream=True)
                return
            except PermissionError:
                print("Error: Permission Denied")
                error_stream_id = quic_connection.get_next_available_stream_id()
                quic_connection.send_stream_data(error_stream_id, b"ERROR:Permission Denied", end_stream=True)
                return

            # Wait a bit to ensure the data is sent
            await asyncio.sleep(0.1)

            # Send connection termination request on a new stream
            termination_stream_id = quic_connection.get_next_available_stream_id()
            quic_connection.send_stream_data(termination_stream_id, b"CONN_TERMINATE", end_stream=True)
            await protocol.data_received.wait()
            print("Server response:", protocol.received_data.decode())

        else:
            print("Connection was not acknowledged. Terminating.")


if __name__ == "__main__":
    asyncio.run(send_data())
