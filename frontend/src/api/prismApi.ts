import axios from "axios";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
} from "../types/prism";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

export async function analyzeProduct(
  payload: AnalyzeRequest
): Promise<AnalyzeResponse> {

  const response = await api.post(
    "/api/v1/analyze",
    payload
  );

  return response.data;
}