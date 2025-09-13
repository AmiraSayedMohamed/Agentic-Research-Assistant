import React, { useState } from "react"

export default function CrossmintNFTMint() {
  const [metadata, setMetadata] = useState({
    name: "",
    description: "",
    image: ""
  })
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  async function handleMint() {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch("/api/mint_nft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(metadata)
      })
      if (!res.ok) throw new Error("Minting failed")
      const data = await res.json()
      setResult(data)
    } catch (err) {
  setResult({ error: (err as Error).toString() })
    }
    setLoading(false)
  }

  return (
    <div className="border p-4 rounded mb-4">
      <h3 className="font-bold mb-2">Mint NFT (Crossmint)</h3>
      <input
        className="border rounded p-2 mb-2 w-full"
        placeholder="Name"
        value={metadata.name}
        onChange={e => setMetadata({ ...metadata, name: e.target.value })}
      />
      <input
        className="border rounded p-2 mb-2 w-full"
        placeholder="Description"
        value={metadata.description}
        onChange={e => setMetadata({ ...metadata, description: e.target.value })}
      />
      <input
        className="border rounded p-2 mb-2 w-full"
        placeholder="Image URL"
        value={metadata.image}
        onChange={e => setMetadata({ ...metadata, image: e.target.value })}
      />
      <button onClick={handleMint} disabled={loading} className="bg-green-600 text-white px-4 py-2 rounded">
        {loading ? "Minting..." : "Mint NFT"}
      </button>
      {result && (
        <div className="mt-4">
          <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}
