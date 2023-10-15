import logging
import json


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def success():
    logger.info("Success")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Image uploaded",
        }),
    }


def not_message():
    logger.warning("Not message")
    return {
        "statusCode": 204,
        "body": json.dumps({
            "message": "No message",
        }),
    }


def not_image():
    logger.warning("Not image")
    return {
        "statusCode": 204,
        "body": json.dumps({
            "message": "No image",
        }),
    }


def message_format_error(err_message):
    logger.error(err_message)
    return {
        "statusCode": 400,
        "body": json.dumps({
            "message": "Message format error",
        }),
    }


def internal_error(err_message):
    logger.error(err_message)
    return {
        "statusCode": 500,
        "body": json.dumps({
            "message": f"Internal error.\n {err_message}",
        }),
    }
