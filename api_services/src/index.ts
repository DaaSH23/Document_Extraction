import express from "express";
import { errorHandler } from "./middleware/errorHandler";
import uploadDocRoutes from "./routes/docRoute";
import cors from 'cors'

const app = express();
const PORT = 3000;

app.use(cors({ origin: 'http://localhost:5173' }));

app.use(errorHandler);
app.use("/api", uploadDocRoutes);

app.listen(PORT, ()=> {
    console.log(`Server running at PORT: ${PORT}`);
});