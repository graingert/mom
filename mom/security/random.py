#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
:module: mom.security.random
:synopsis: Random number, bits, bytes, and string generation utilities.

Bits and bytes
---------------------------
.. autofunction:: generate_random_bits
.. autofunction:: generate_random_bytes

Numbers
-------
.. autofunction:: generate_random_ulong_atmost
.. autofunction:: generate_random_ulong_exactly
.. autofunction:: generate_random_ulong_between

Strings
-------
.. autofunction:: generate_random_hex_string
"""

from __future__ import absolute_import

__all__ = [
    "generate_random_bits",
    "generate_random_bytes",
    "generate_random_hex_string",
    "generate_random_ulong_atmost",
    "generate_random_ulong_exactly",
    "generate_random_ulong_between",
    ]

import os
from mom.builtins import long_bit_length, is_integer
from mom.codec import \
    hex_encode, \
    bytes_to_long


try:
    # Operating system unsigned random.
    os.urandom(1)
    def generate_random_bytes(count):
        """
        Generates a random byte string with ``count`` bytes.

        :param count:
            Number of bytes.
        :returns:
            Random byte string.
        """
        return os.urandom(count)
except AttributeError:
    try:
        __urandom_device__ = open("/dev/urandom", "rb")
        def generate_random_bytes(count):
            """
            Generates a random byte string with ``count`` bytes.

            :param count:
                Number of bytes.
            :returns:
                Random byte string.
            """
            return __urandom_device__.read(count)
    except IOError:
        #Else get Win32 CryptoAPI PRNG
        try:
            import win32prng
            def generate_random_bytes(count):
                """
                Generates a random byte string with ``count`` bytes.

                :param count:
                    Number of bytes.
                :returns:
                    Random byte string.
                """
                random_bytes = win32prng.generate_random_bytes(count)
                assert len(random_bytes) == count
                return random_bytes
        except ImportError:
            # What the fuck?!
            def generate_random_bytes(_):
                """
                WTF.

                :returns:
                    WTF.
                """
                raise NotImplementedError("What the fuck?! No PRNG available.")


def generate_random_bits(n_bits, rand_func=generate_random_bytes):
    """
    Generates the specified number of random bits as a byte string.
    For example::

        f(x) -> y such that
        f(16) ->           1111 1111 1111 1111; bytes_to_long(y) => 65535L
        f(17) -> 0000 0001 1111 1111 1111 1111; bytes_to_long(y) => 131071L

    :param n_bits:
        Number of random bits.

        if n is divisible by 8, (n / 8) bytes will be returned.
        if n is not divisible by 8, ((n / 8) + 1) bytes will be returned
        and the prefixed offset-byte will have `(n % 8)` number of random bits,
        (that is, `8 - (n % 8)` high bits will be cleared).

        The range of the numbers is 0 to (2**n)-1 inclusive.
    :param rand_func:
        Random bytes generator function.
    :returns:
        Bytes.
    """
    if not is_integer(n_bits):
        raise TypeError("unsupported operand type: %r" % type(n_bits).__name__)
    if n_bits <= 0:
        raise ValueError("number of bits must be greater than 0.")
    # Doesn't perform any floating-point operations.
    q, r = divmod(n_bits, 8)
    random_bytes = rand_func(q)
    if r:
        offset = ord(rand_func(1)) >> (8 - r)
        random_bytes = chr(offset) + random_bytes
    return random_bytes


def generate_random_ulong_atmost(n_bits, rand_func=generate_random_bytes):
    """
    Generates a random unsigned long with `n_bits` random bits.

    :param n_bits:
        Number of random bits to be generated at most.
    :param rand_func:
        Random bytes generator function.
    :returns:
        Returns an unsigned long integer with at most `n_bits` random bits.
        The generated unsigned long integer will be between 0 and
        (2**n_bits)-1 both inclusive.
    """
    if not is_integer(n_bits):
        raise TypeError("unsupported operand type: %r" % type(n_bits).__name__)
    if n_bits <= 0:
        raise ValueError("number of bits must be greater than 0.")
    # Doesn't perform any floating-point operations.
    q, r = divmod(n_bits, 8)
    if r:
        q += 1
    random_bytes = rand_func(q)
    mask = (1L << n_bits) - 1
    return mask & bytes_to_long(random_bytes)


def generate_random_ulong_exactly(n_bits, rand_func=generate_random_bytes):
    """
    Generates a random unsigned long with `n_bits` random bits.

    :param n_bits:
        Number of random bits.
    :param rand_func:
        Random bytes generator function.
    :returns:
        Returns an unsigned long integer with `n_bits` random bits.
        The generated unsigned long integer will be between 2**(n_bits-1) and
         (2**n_bits)-1 both inclusive.
    """
    # Doesn't perform any floating-point operations.
    value = bytes_to_long(generate_random_bits(n_bits, rand_func=rand_func))
    #assert(value >= 0 and value < (2L ** n_bits))
    # Set the high bit to ensure bit length.
    #value |= 2L ** (n_bits - 1)
    value |= 1L << (n_bits - 1)
    #assert(long_bit_length(value) >= n_bits)
    return value


# Taken from PyCrypto.
def generate_random_ulong_between(low, high, rand_func=generate_random_bytes):
    """
    Generates a random long integer between low and high, not including high.

    :param low:
        Low
    :param high:
        High
    :param rand_func:
        Random bytes generator function.
    :returns:
        Random unsigned long integer value.
    """
    if not (is_integer(low) and is_integer(high)):
        raise TypeError("unsupported operand types(s): %r and %r" \
                        % (type(low).__name__, type(high).__name__))
    if low >= high:
        raise ValueError("high value must be greater than low value.")
    r = high - low - 1
    bits = long_bit_length(r)
    value = generate_random_ulong_atmost(bits, rand_func=rand_func)
    while value > r:
        value = generate_random_ulong_atmost(bits, rand_func=rand_func)
    return low + value


def generate_random_hex_string(length=8, rand_func=generate_random_bytes):
    """
    Generates a random ASCII-encoded hexadecimal string of an even length.

    :param length:
        Length of the string to be returned. Default 32.
        The length MUST be a positive even number.
    :param rand_func:
        Random bytes generator function.
    :returns:
        A string representation of a randomly-generated hexadecimal string.
    """
    #if length % 2 or length <= 0:
    if length & 1L or length <= 0:
        raise ValueError(
            "This function expects a positive even number "\
            "length: got length `%r`." % length)
    return hex_encode(rand_func(length/2))
