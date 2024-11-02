// Error handler middleware

import { Request, Response, NextFunction } from "express";
import { CustomError } from "../utils/customError";


export const errorHandler = (err: CustomError, req: Request, res: Response, next: NextFunction) => {

    // default values for unknown errors
    const statusCode = err.statusCode || 500;
    const message = err.message || "An unexpected error occurred.";

    res.status(statusCode).json({
        success: false,
        message,
        ...(err.details && { details: err.details }),
    });
};