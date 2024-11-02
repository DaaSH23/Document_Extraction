import { Request, Response, NextFunction } from "express";

type AsyncFunction = (
    req: Request,
    res: Response,
    next: NextFunction
) => Promise<any>;

export const catchAsyncError = (passedFunction: AsyncFunction) => {
    return (req: Request, res: Response, next: NextFunction) => {
        Promise.resolve(passedFunction(req, res, next)).catch(next);
    }
}