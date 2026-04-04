import smtplib
import socket

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        if timeout is not None and not timeout:
            raise ValueError("Non-blocking socket (timeout=0) is not supported")

        last_error = None
        for _family, _socktype, _proto, _canonname, sockaddr in socket.getaddrinfo(
            host,
            port,
            socket.AF_INET,
            socket.SOCK_STREAM,
        ):
            try:
                return socket.create_connection(sockaddr, timeout, self.source_address)
            except OSError as exc:
                last_error = exc

        if last_error is not None:
            raise last_error

        raise OSError(f"No se pudo resolver una direccion IPv4 para {host}")


class IPv4SMTP_SSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        if timeout is not None and not timeout:
            raise ValueError("Non-blocking socket (timeout=0) is not supported")

        last_error = None
        for _family, _socktype, _proto, _canonname, sockaddr in socket.getaddrinfo(
            host,
            port,
            socket.AF_INET,
            socket.SOCK_STREAM,
        ):
            try:
                new_socket = socket.create_connection(sockaddr, timeout, self.source_address)
                return self.context.wrap_socket(new_socket, server_hostname=self._host)
            except OSError as exc:
                last_error = exc

        if last_error is not None:
            raise last_error

        raise OSError(f"No se pudo resolver una direccion IPv4 para {host}")


class EmailBackend(SMTPEmailBackend):
    @property
    def connection_class(self):
        return IPv4SMTP_SSL if self.use_ssl else IPv4SMTP
