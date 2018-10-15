"""Implementation of custom session system.

Credit for this can go to the warehouse project where I find how to implement
custom session system with redis.

Differences are noted:
 - Warehouse use it's own implementation for the TimestampSigner and
    BadSignature
 - The factory session does not initialize Redis exactly the same way
 - there is currently no equivalent to their InvalidSession
"""
import os
import time
import base64
import functools

from typing import (
    Optional,
    Callable,
)

import redis
import msgpack
from itsdangerous import TimestampSigner, BadSignature

from pyramid.request import Request
from pyramid.response import Response
from pyramid.interfaces import ISession, ISessionFactory

from zope.interface import implementer


def _create_token() -> str:
    """Create a new base 64 token."""
    token = base64.urlsafe_b64encode(os.urandom(32).rstrip(b'='))
    return token.decode('utf-8')

def _changed_method(method: Callable) -> Callable:
    @functools.wraps(method)
    def wrapped(self, *args, **kwargs):
        self.changed()
        return method(self, *args, **kwargs)
    return wrapped


@implementer(ISession)
class PVaultSession(dict):
    """PVault session.
    
    This class is the representation of a session. This class act as a
    dictionary. You can add / remove element using dict syntax:

    - **add** : sesssion['key'] = value
    - **remove** : del session['key']

    Session in pyramid also have flash messages (more informations
    `here <https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/sessions.html>`_)
    """

    _csrf_token_key = "_csrf_token"
    _flash_key = "_flash_messages"

    # A number of our methods need to be decorated so that they also call
    # self.changed()
    __delitem__ = _changed_method(dict.__delitem__)
    __setitem__ = _changed_method(dict.__setitem__)
    clear = _changed_method(dict.clear)
    pop = _changed_method(dict.pop)
    popitem = _changed_method(dict.popitem)
    setdefault = _changed_method(dict.setdefault)
    update = _changed_method(dict.update)

    def __init__(self, data:dict={}, session_id:Optional[str]=None, new:bool=True) -> None:
        """Contructor of the class.

        This function initialize the data if data is None and initialize some
        attributes.

        :param data: data dictionary
        :type data: dict
        :param session_id: the session id if available
        :type session_id: str
        :param new: boolean to indication if the session is a new session
        :type new: bool
        """
        super(PVaultSession, self).__init__(data)
        self._sid = session_id
        self._changed = False
        self.new = new
        self.created = int(time.time())

        # We'll track all of the IDs that have been invalidated here
        self.invalidated = set()

    @property
    def sid(self) -> str:
        """Create the session id if not present, and return it.

        :return: return the session id
        :rtype: str
        """
        if self._sid is None:
            self._sid = _create_token()
        return self._sid

    def invalidate(self) -> None:
        """Invalidate the session."""
        self.clear()
        self.new = True
        self.created = int(time.time())
        self._changed = False

        # If the current session id isn't None we'll want to record it as one
        # of the ones that have been invalidated.
        if self._sid is not None:
            self.invalidated.add(self._sid)
            self._sid = None

    def should_save(self) -> bool:
        """Return true if the session must be save, ortherwise return false.

        If the session has been changed then the session must be backed up
        again with the new information.

        :return: return true if the session has changed
        :rtype: bool
        """
        return self._changed

    def changed(self) -> None:
        """Set the status changed to True."""
        self._changed = True

    def _get_flash_queue_key(self, queue: str) -> str:
        # TODO: Verify the type of queue
        """Function to generate the flash queue key.

        :param queue: the queue
        :type queue: str
        """
        return '.'.join(filter(None, [self._flash_key, queue]))

    def flash(self, msg, queue:str='', allow_duplicate:bool=True) -> None:
        """Function to add a message to the flash queue.

        :param msg: The message to add to the queue
        :type msg: str
        :param queue: The queue to use, default queue is used if not
            specified
        :type queue: str
        :param allow_duplicate: If false the same message is not readded if
            it's present on the queue
        :type allow_duplicate: bool
        """
        queue_key = self._get_flash_queue_key(queue)

        # If we're not allowing duplicates check if this message is already
        # in the queue, and if it is just return immediately.
        if not allow_duplicate and msg in self[queue_key]:
            return

        self.setdefault(queue_key, []).append(msg)

    def pop_flash(self, queue='') -> list:
        """Pop the message(s) from specifique queue and return them.

        Message(s) get with this method are removed from the queue.

        :param queue: the queue where we want to remove message from.
        :type queue: str
        :return: the list of messages or empty list.
        :rtype: list
        """
        queue_key = self._get_flash_queue_key(queue)
        messages = self.pop(queue_key, [])
        return messages

    def peek_flash(self, queue='') -> list:
        """Peek the message(s) from queue and return them.

        Message(s) get with this method are not removed from the queue.

        :param queue: the queue where we want to remove message from.
        :type queue: str
        :return: the list of messages or empty list.
        :rtype: list
        """
        queue_key = self._get_flash_queue_key(queue)
        messages = self.get(queue_key, [])
        return messages

@implementer(ISessionFactory)
class PVaultSessionFactory(object):
    """PVaultSession factory."""

    cookie_name = 'session_id'
    max_age = 12 * 60 * 60  # 12 hours

    def __init__(self, secret:str, redis_host:str, redis_port:str) -> None:
        self.redis = redis.StrictRedis(host=redis_host, port=redis_port)
        self.signer = TimestampSigner(secret, salt='session')

    def __call__(self, request:Request) -> PVaultSession:
        return self._process_request(request)

    def _redis_key(self, session_id: str) -> str:
        return f'pvault/session/data/{session_id}'

    def _process_request(self, request:Request) -> PVaultSession:
        # Register a callback with the request so we can save the session once
        # it's finished.
        request.add_response_callback(self._process_response)

        # Load our session ID from the request.
        session_id = request.cookies.get(self.cookie_name)

        # If we do not have a session ID then we'll just use a new empty
        # session.
        if session_id is None:
            return PVaultSession()

        # Check to make sure we have a valid session id
        try:
            session_id = self.signer.unsign(session_id, max_age=self.max_age)
            session_id = session_id.decode('utf8')
        except BadSignature:
            return PVaultSession()

        # Fetch the serialized data from redis
        bdata = self.redis.get(self._redis_key(session_id))

        # If the session didn't exist in redis, we'll give the user a new
        # session.
        if bdata is None:
            return PVaultSession()

        # De-serialize our session data
        try:
            data = msgpack.unpackb(bdata, encoding='utf8', use_list=True)
        except msgpack.exceptions.ExtraData:
            # If the session data was invalid we'll give the user a new session
            return PVaultSession()
        except msgpack.exceptions.UnpackException:
            # If the session data was invalid we'll give the user a new session
            return PVaultSession()

        # If we were able to load existing session data, load it into a
        # Session class
        session = PVaultSession(data, session_id, False)
        return session
        # return

    def _process_response(self, request:Request, response:Response) -> None:
        # If the request has an InvalidSession, then the view can't have
        # accessed the session, and we can just skip all of this anyways.
        # if isinstance(request.session, InvalidSession):
        #     return

        # Check to see if the session has been marked to be deleted, if it has
        # benn then we'll delete it, and tell our response to delete the
        # session cookie as well.
        if request.session.invalidated:
            for session_id in request.session.invalidated:
                self.redis.delete(self._redis_key(session_id))

            if not request.session.should_save():
                response.delete_cookie(self.cookie_name)

        # Check to see if the session has been marked to be saved, generally
        # this means that the session data has been modified and thus we need
        # to store the new data.
        if request.session.should_save():
            # Save our session in Redis
            self.redis.setex(
                self._redis_key(request.session.sid),
                self.max_age,
                msgpack.packb(
                    request.session,
                    encoding='utf8',
                    use_bin_type=True
                ),
            )

            # Send our session cookie to the client
            response.set_cookie(
                self.cookie_name,
                self.signer.sign(request.session.sid.encode('utf8')),
                max_age=self.max_age,
                httponly=True,
                secure=request.scheme == 'https',
                samesite=b'lax',
            )
