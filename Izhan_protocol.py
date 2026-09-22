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
MAX_SPLITS = {CM: 2, EE: 2, DP: 1, SC: 1}

# How many fields each packet type should have (CC can be 0 or 1)
FIELD_COUNTS = {SS: [3], CC: [0, 1], EC: [3], CM: [2], DP: [1], SC: [0], EE: [2], END: [0]}


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
        if secure not in ("0", "1"):
            raise ValueError("Secure flag must be 0 or 1")

    return True


if __name__ == "__main__":
    p = create_packet(SS, PROTOCOL_NAME, PROTOCOL_VERSION, 0)
    print(p)
    print(parse_packet(p))
    print(parse_packet("(CM, prompt, mkdir a,b)"))
    print(parse_packet("(DP, Hello, World)"))
    print(parse_packet("(End)"))

    print(validate_packet(*parse_packet("(SS,RFMP,v1.0,0)")))   # True
    print(validate_packet(*parse_packet("(CM,prompt,ls)")))     # True
    try:
        validate_packet(*parse_packet("(SS,WRONG,v1.0,0)"))
    except ValueError as e:
        print("caught:", e)