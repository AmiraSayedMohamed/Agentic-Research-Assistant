import React, { useRef, useState } from "react";
import { Button } from "@/components/ui/button";

export default function PDFUpload({ onUpload }: { onUpload?: (file: File) => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0] || null;
      if (!file) return;
      setSelectedFile(file);
      setUploading(true);
      setError(null);
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("query", "uploaded via UI");
        formData.append("user_id", "frontend");
        const response = await fetch("http://localhost:8000/upload_pdf", {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          throw new Error("Upload failed");
        }
        setError(null);
        alert("PDF uploaded successfully!");
        if (onUpload) onUpload(file);
      } catch (err: any) {
        setError(err.message || "Upload failed");
      } finally {
        setUploading(false);
      }
    };

  return (
  <div className="flex flex-col items-center gap-8 mt-8">
      <label htmlFor="pdf-upload">
        <Button asChild className="bg-purple-600 text-white" disabled={uploading}>
          <span>{uploading ? "Uploading..." : "Upload PDF"}</span>
        </Button>
      </label>
      <input
        id="pdf-upload"
        type="file"
        accept="application/pdf"
        style={{ display: "none" }}
        onChange={handleUpload}
      />
      {selectedFile && <span className="text-sm">Selected: {selectedFile.name}</span>}
      {error && <span className="text-red-500 text-sm">{error}</span>}
    </div>
  );
}
