import express from "express";
import multer from 'multer';
import bodyParser from "body-parser";
import { processDocument } from "../controller/uploadDoc";

const routes = express.Router();
const upload = multer();

// Routes
routes.post('/extractInfo', upload.single('image'), bodyParser.json(), processDocument);

export default routes;