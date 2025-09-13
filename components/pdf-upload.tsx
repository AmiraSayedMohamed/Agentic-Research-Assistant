import React, { useRef, useState } from "react";
import { Button } from "@/components/ui/button";

export default function PDFUpload({ onUpload }: { onUpload?: (file: File) => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
    setError(null);
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError("Please select a PDF file.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const response = await fetch("/api/upload_pdf", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error("Upload failed");
      }
      if (onUpload) onUpload(selectedFile);
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <input
        type="file"
        accept="application/pdf"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleFileChange}
      />
      <Button onClick={handleButtonClick} variant="outline">
        Select PDF
      </Button>
      {selectedFile && <span className="text-sm">Selected: {selectedFile.name}</span>}
      <Button onClick={handleUpload} disabled={uploading || !selectedFile} className="bg-purple-600 text-white">
        {uploading ? "Uploading..." : "Upload PDF"}
      </Button>
      {error && <span className="text-red-500 text-sm">{error}</span>}
    </div>
  );
}
