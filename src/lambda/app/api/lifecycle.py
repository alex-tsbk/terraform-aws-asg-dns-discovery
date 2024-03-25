from __future__ import annotations

import json
from typing import Any

from app.observability.logging import get_logger, to_json
from app.services.lifecycle_service import LifecycleService


def lambda_handler(event: dict, context: Any) -> None:
    """Lambda handler function to be invoked by AWS SNS

    Args:
        event [dict]: Example of event object passed to the handler
            {
                "Records": [
                    {
                        "EventSource": "aws:sns",
                        "EventVersion": "1.0",
                        "EventSubscriptionArn": "arn:aws:sns:us-west-2:123456789012:dev-asg-service-discovery:a65f61f6-91f5-49c9-b5cb-ef64bd0889d1",
                        "Sns": {
                            "Type": "Notification",
                            "MessageId": "9c35aaf3-945c-529d-93c8-f4a58fd8b177",
                            "TopicArn": "arn:aws:sns:us-west-2:123456789012:dev-asg-service-discovery",
                            "Subject": "Auto Scaling:  Lifecycle action 'TERMINATING' for instance i-03a2b505b266b2eaa in progress.",
                            "Message": "<json string>",
                            "Timestamp": "2024-02-26T04:53:24.658Z",
                            "SignatureVersion": "1",
                            "Signature": "...",
                            "SigningCertUrl": "...",
                            "UnsubscribeUrl": "...",
                            "MessageAttributes": {}
                        }
                    }
                ]
            }

        context [Any]: Lambda context object
    """
    logger = get_logger()
    sns_message = None
    logger.debug(f"Received event: {to_json(event)}")
    # Extract Message from Records -> SNS
    if "Records" in event and len(event["Records"]) > 0 and "Sns" in event["Records"][0]:
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
        logger.debug(f"Extracted ['Records'][0]['Sns']['Message']: {to_json(sns_message)}")

    # If no SNS message found, return 500
    if not sns_message:
        logger.warning("No SNS event found in the event object")
        return {"statusCode": 500, "body": "No SNS event found in the event object"}

    # If this is a test notification, return 200 OK
    if (sns_event := sns_message.get("Event", "")) and sns_event == "autoscaling:TEST_NOTIFICATION":
        logger.info("Received test notification event")
        return {"statusCode": 200, "body": "Test notification received"}

    # We received an SNS message but it's not a lifecycle event
    if "LifecycleTransition" not in sns_message:
        logger.warning("No lifecycle transition found in the SNS message. Ignoring...")
        return {"statusCode": 400, "body": "No lifecycle transition found in the SNS message"}

    # Build lifecycle event model
    try:
        event: LifecycleEventModel = lifecycle_event_model_factory.create(sns_message)
    except Exception as e:
        raise BusinessException(f"Error creating lifecycle event model: {str(e)}") from e

    # Looks like we have a lifecycle event, let's handle it
    logger.debug("Initializing lifecycle service handling...")
    try:
        lifecycle_service = LifecycleService()
        logger.info(
            f"Handling lifecycle event for AutoScalingGroup: {sns_message['AutoScalingGroupName']} and EC2 instance: {sns_message['EC2InstanceId']}"
        )
        result = lifecycle_service.handle(sns_message)
    except Exception as e:
        # TODO: Submit failure data point to CloudWatch
        logger.error(f"Error handling lifecycle event: {str(e)}")
        return {"statusCode": 500, "body": "Error handling lifecycle event"}
    else:
        if result:
            logger.info("Lifecycle event handled successfully")
        else:
            logger.warning("Lifecycle event not handled")

    return {"statusCode": 200, "handled": result, "body": "Lifecycle action completed"}
