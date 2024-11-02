// service to upload documents and request OCR process

import { Response, Request, NextFunction, json } from "express"
import { catchAsyncError } from "../middleware/catchAsyncError"
import { CustomError } from "../utils/customError";
import { publisherClient, subscriberClient } from "../redisClient";

export const processDocument = catchAsyncError(async(req: Request, res: Response, next: NextFunction) => {
    // const { document } = req.body;
    const taskId = `task-${Date.now()}`;

    if(!req.file){
        throw new CustomError("Document data is missing", 400);
    };

    const document = req.file.buffer.toString("base64");


    // pushing task to the redis queue
    await publisherClient.lpush("ocr_queue", JSON.stringify({taskId, document}));

    subscriberClient.subscribe(`ocr_result_${taskId}`, (err) => {
        if(err){
            throw new CustomError("Failed to subscribe to OCR result", 500, err);
        }
    });

    subscriberClient.on("message", (channel, message) => {
        if(channel === `ocr_result_${taskId}`) {
            res.json({taskId, result: JSON.parse(message)});
            subscriberClient.unsubscribe(channel);
        }
    });

});