import asyncio
import sys
from aioquic.asyncio import serve
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class QSFTPServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.authenticated = False
        self.file_receiving = False
        self.received_file = None
        self.received_file_name = None

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            if not self.authenticated:
                data = event.data.decode()
                if data.startswith("CONN_REQUEST"):
                    self.handle_connection_request(event.stream_id, data)
                elif data.startswith("CONN_TERMINATE"):
                    self.handle_connection_termination(event.stream_id, data)
                elif data.startswith("ERROR"):
                    self.handle_error(event.stream_id, data)
                else:
                    self.send_error(event.stream_id, "Unauthorized or unexpected data")
            else:
                self.handle_file_data(event.stream_id, event.data, event.end_stream)

    def handle_connection_request(self, stream_id, data):
        print("Connection request received.")
        self.authenticated = True  # Simplified for this example
        try:
            self.received_file_name = data.split(":")[1]
            self.received_file = open(self.received_file_name, "wb")
        except PermissionError:
            self.send_error(stream_id, "Permission Denied")
            return
        response = "CONN_ACK"
        self._quic.send_stream_data(stream_id, response.encode(), end_stream=True)
        print("Connection acknowledged.")

    def handle_connection_termination(self, stream_id, data):
        print("Connection termination request received.")
        response = "CONN_TERMINATED"
        self._quic.send_stream_data(stream_id, response.encode(), end_stream=True)
        print("Connection terminated.")
        self._quic.close()

    def handle_error(self, stream_id, data):
        print(f"Error received: {data}")

    def handle_file_data(self, stream_id, data, end_stream):
        print("Receiving file data...")
        try:
            self.received_file.write(data)
        except IOError:
            self.send_error(stream_id, "File Write Error")
            return
        if end_stream:
            self.received_file.close()
            self.file_receiving = False
            print("File reception completed.")

    def send_error(self, stream_id, error_message):
        error_pdu = f"ERROR:{error_message}"
        self._quic.send_stream_data(stream_id, error_pdu.encode(), end_stream=True)
        print(f"Error sent: {error_message}")


async def run_server():
    configuration = QuicConfiguration(is_client=False)
    try:
        configuration.load_cert_chain("cert.pem", "key.pem")
        print("Server is attempting to start...")
        server = await serve('localhost', 5000, configuration=configuration, create_protocol=QSFTPServerProtocol)
        print("Server started successfully.")

        while True:
            await asyncio.sleep(3600)  # keep the server running
    except Exception as e:
        print(f"Server failed to start: {e}")


if __name__ == "__main__":
    print("Starting QSFTP Server...")
    asyncio.run(run_server())
    print("Server shutdown.")
