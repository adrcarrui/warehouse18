from enum import Enum


class MovementType(str, Enum):
    GOOD_RECEIPT = "Good receipt"
    GOOD_ISSUE = "Good issue"
    GOOD_TRANSFER = "Good transfer"
    GOOD_TRACKING = "Good tracking"

class SpecialLocation(str, Enum):
    REPAIR_CENTRE = "Repair Centre"
    DEVICE = "Device"
    SUPPLIER = "Supplier"
    CALIBRATION = "Calibration"
    UNKNOWN = "Unknown"
    ZAL = "ZAL"
    OUT_OF_SYSTEM = "Out of system"
    LOAN = "Loan"
    COURSE = "Course"
