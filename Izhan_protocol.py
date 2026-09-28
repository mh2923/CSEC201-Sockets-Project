# Izhan_protocol.py
# Shared packet definitions for the client and server.

PROTOCOL_NAME = "RFMP"
PROTOCOL_VERSION = "v1.0"

# Packet types
SS = "SS"      # start
CC = "CC"      # confirm connection
EC = "EC"      # encryption
CM = "CM"      # command
DP = "DP"      # data
SC = "SC"      # successful
EE = "EE"      # exception
END = "End"    # closing

PACKET_TYPES = [SS, CC, EC, CM, DP, SC, EE, END]

# Packets that end with free text (which may contain commas)
# are only split a limited number of times.
MAX_SPLITS = {CM: 2, EE: 2, DP: 1, SC: 1, CC: 1, EC: 3}

# How many fields each packet type should have (CC and SC can be 0 or 1)
FIELD_COUNTS = {SS: [3], CC: [0, 1], EC: [3], CM: [2], DP: [1], SC: [0, 1], EE: [2], END: [0]}

# encryption algorithms that can go in an EC packet
ALGORITHMS = ["AES", "Caesar"]

# error codes we're using (max 4, as allowed by the brief)
ERROR_CODES = {
    "E1": "File not found",
    "E2": "Permission denied",
    "E3": "Invalid command or arguments",
    "E4": "Unknown error",
}


def create_packet(packet_type, *fields):
    """Build a packet string, e.g. "(SS,RFMP,v1.0,0)"."""
    if packet_type not in PACKET_TYPES:
        raise ValueError("Unknown packet type: " + packet_type)

    parts = [packet_type] + [str(f) for f in fields]
    return "(" + ",".join(parts) + ")"


def parse_packet(packet):
    """Split a packet string into (type, [fields])."""
    packet = packet.strip()
    if not (packet.startswith("(") and packet.endswith(")")):
        raise ValueError("Packet must start with ( and end with )")

    body = packet[1:-1]

    packet_type = body.split(",")[0].strip()
    if packet_type not in PACKET_TYPES:
        raise ValueError("Unknown packet type: " + packet_type)

    parts = body.split(",", MAX_SPLITS.get(packet_type, -1))

    # Data text is kept exactly as sent
    if packet_type == DP:
        text = parts[1] if len(parts) > 1 else ""
        if text.startswith(" "):
            text = text[1:]
        return packet_type, [text]

    return packet_type, [p.strip() for p in parts[1:]]


def validate_packet(packet_type, fields):
    """Check a parsed packet's fields make sense for its type.
    Returns True if OK, otherwise raises ValueError."""
    if packet_type not in PACKET_TYPES:
        raise ValueError("Unknown packet type: " + packet_type)

    if packet_type in FIELD_COUNTS:
        if len(fields) not in FIELD_COUNTS[packet_type]:
            raise ValueError(packet_type + " packet has the wrong number of fields")

    if packet_type == SS:
        protocol, version, secure = fields
        if protocol != PROTOCOL_NAME:
            raise ValueError("Unexpected protocol name: " + protocol)
        if version != PROTOCOL_VERSION:
            raise ValueError("Unexpected protocol version: " + version)
        if secure not in ("0", "1"):
            raise ValueError("Secure flag must be 0 or 1")

    if packet_type == EC:
        if fields[0] not in ALGORITHMS:
            raise ValueError("Unknown algorithm: " + fields[0])
        if ":" not in fields[2]:
            raise ValueError("Last EC field must be username:public_key")

    return True


def handle_open_read(filename):
    # returns (True, contents) if it worked, or (False, (code, message)) if not
    try:
        with open(filename, "r") as f:
            return True, f.read()
    except FileNotFoundError:
        return False, ("E1", "File not found: " + filename)
    except PermissionError:
        return False, ("E2", "Permission denied: " + filename)
    except Exception as e:
        return False, ("E4", str(e))


def handle_open_write(filename, data):
    # creates/overwrites the file, returns (True, message) or (False, (code, message))
    try:
        with open(filename, "w") as f:
            f.write(data)
        return True, "Data written to " + filename
    except PermissionError:
        return False, ("E2", "Permission denied: " + filename)
    except Exception as e:
        return False, ("E4", str(e))


def make_success_packet(message=""):
    if message:
        return create_packet(SC, message)
    return create_packet(SC)


def make_error_packet(error_code, description):
    return create_packet(EE, error_code, description)


def caesar_encrypt(text, key):
    # shifts letters by key, everything else (spaces, numbers, symbols) stays the same
    result = ""
    for ch in text:
        if "A" <= ch <= "Z":
            result += chr((ord(ch) - ord("A") + key) % 26 + ord("A"))
        elif "a" <= ch <= "z":
            result += chr((ord(ch) - ord("a") + key) % 26 + ord("a"))
        else:
            result += ch
    return result


def caesar_decrypt(text, key):
    # decrypting is just shifting the other way
    return caesar_encrypt(text, -key)


def caesar_shift_from_key(session_key):
    # session key is bytes but Caesar needs a small number,
    # so both sides turn the same key into the same shift (1 to 25)
    return sum(session_key) % 25 + 1


def make_ec_packet(algorithm, encrypted_session_key, username, client_public_key):
    # last field is username:public_key, as in the brief
    return create_packet(EC, algorithm, encrypted_session_key, username + ":" + client_public_key)


def read_ec_fields(fields):
    # splits the fields of a parsed EC packet into 4 separate values
    algorithm = fields[0]
    encrypted_session_key = fields[1]
    username, client_public_key = fields[2].split(":", 1)
    return algorithm, encrypted_session_key, username, client_public_key
