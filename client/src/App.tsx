import { useState } from 'react';
import './App.css';
import ImageUploadPreview from './components/uploadComponent';

// Define the type for uploadStatus state
interface UploadStatus {
  isLoading: boolean;
  error: string | null;
  successUrl: string | null;
  extractedData: Record<string, any> | null;
}

function App() {
  // Set initial state for upload status with type UploadStatus
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    isLoading: false,
    error: null,
    successUrl: null,
    extractedData: null,
  });

  // Define the type of file for the parameter
  const handleImageUpload = async (file: File): Promise<string | void> => {
    setUploadStatus({
      isLoading: true,
      error: null,
      successUrl: null,
      extractedData: null,
    });

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch('http://localhost:3000/api/extractInfo', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload image');
      }

      const data = await response.json();
      console.log(data);

      setUploadStatus({
        isLoading: false,
        error: null,
        successUrl: data.url,
        extractedData: data.result,
      });

      return data.url;
    } catch (error: any) {
      setUploadStatus({
        isLoading: false,
        error: error.message,
        successUrl: null,
        extractedData: null,
      });
      throw error;
    }
  };

  return (
    <div className="min-h-screen py-12">
      <div className="max-w-7xl mx-auto sm:px-6 lg:px-8">
        <div className="rounded-lg shadow">
          <div className="px-4 py-5 sm:p-6">
            <h1 className="text-2xl font-bold text-white mb-6 text-center">
              Image Upload
            </h1>

            {uploadStatus.error && (
              <div className="mb-4 p-4 bg-red-50 rounded-lg">
                <p className="text-red-600">{uploadStatus.error}</p>
              </div>
            )}

            <ImageUploadPreview
              onUpload={handleImageUpload}
              isUploading={uploadStatus.isLoading}
            />

            {uploadStatus.successUrl && (
              <div className="mt-4 p-4 bg-green-50 rounded-lg">
                <p className="text-green-700 font-medium">Upload Successful!</p>
                <p className="text-sm text-gray-600 break-all mt-2">
                  URL: {uploadStatus.successUrl}
                </p>
              </div>
            )}

            {/* Display extracted data if available */}
            {uploadStatus.extractedData && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h2 className="text-xl font-semibold text-gray-700 mb-4">
                  Extracted Information
                </h2>
                <ul className="text-sm text-gray-600 space-y-2">
                  <li><strong>Surname:</strong> {uploadStatus.extractedData.Surname}</li>
                  <li><strong>Given Name:</strong> {uploadStatus.extractedData.GivenName}</li>
                  <li><strong>Passport No:</strong> {uploadStatus.extractedData.PassportNo}</li>
                  <li><strong>Nationality:</strong> {uploadStatus.extractedData.Nationality}</li>
                  <li><strong>Sex:</strong> {uploadStatus.extractedData.Sex}</li>
                  <li><strong>Date of Birth:</strong> {uploadStatus.extractedData.DateOfBirth}</li>
                  <li><strong>Place of Birth:</strong> {uploadStatus.extractedData.PlaceOfBirth}</li>
                  <li><strong>Place of Issue:</strong> {uploadStatus.extractedData.PlaceOfIssue}</li>
                  <li><strong>Issue Date:</strong> {uploadStatus.extractedData.IssueDate}</li>
                  <li><strong>Expiry Date:</strong> {uploadStatus.extractedData.ExpiryDate}</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
