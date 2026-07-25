import { useEffect, useRef, useState } from "react"
import { FileText, Paperclip, Trash2, UploadCloud, X } from "lucide-react"
import { forgetDocument, listDocuments, uploadDocument } from "../lib/api"
import type { DocumentSummary } from "../lib/types"

interface DocumentPanelProps {
  activeDocumentId: string | null
  onSelect: (documentId: string | null) => void
}

export function DocumentPanel({ activeDocumentId, onSelect }: DocumentPanelProps) {
  const [open, setOpen] = useState(false)
  const [documents, setDocuments] = useState<DocumentSummary[]>([])
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const refresh = () => {
    listDocuments()
      .then((res) => setDocuments(res.documents))
      .catch(() => setDocuments([]))
  }

  useEffect(() => {
    if (open) refresh()
  }, [open])

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    setUploading(true)

    try {
      const result = await uploadDocument(files[0])
      refresh()
      onSelect(result.document_id)
    } catch {
      // Surfacing upload failures inline would need a toast system;
      // v1 keeps this best-effort and lets the user retry.
    } finally {
      setUploading(false)
    }
  }

  const handleForget = async (documentId: string) => {
    await forgetDocument(documentId)
    if (activeDocumentId === documentId) onSelect(null)
    refresh()
  }

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        title="Attach a document for retrieval-augmented answers"
        className={`flex h-10 w-10 items-center justify-center rounded-full transition ${
          activeDocumentId
            ? "bg-violet-500 text-white"
            : "bg-zinc-100 text-zinc-500 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
        }`}
      >
        <Paperclip size={18} />
      </button>

      {open && (
        <div className="absolute bottom-12 left-0 z-20 w-80 rounded-2xl border border-white/30 bg-white/70 p-3 shadow-xl backdrop-blur-xl dark:border-white/10 dark:bg-zinc-900/70">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold text-zinc-500">Documents</span>
            <button onClick={() => setOpen(false)} className="text-zinc-400 hover:text-zinc-600">
              <X size={14} />
            </button>
          </div>

          <div
            onDragOver={(e) => {
              e.preventDefault()
              setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDragOver(false)
              handleFiles(e.dataTransfer.files)
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed p-4 text-center text-xs transition ${
              dragOver
                ? "border-violet-400 bg-violet-400/10 text-violet-500"
                : "border-zinc-300 text-zinc-400 dark:border-zinc-700"
            }`}
          >
            <UploadCloud size={18} />
            {uploading ? "Uploading..." : "Drop a file or click to upload"}
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>

          {documents.length > 0 && (
            <ul className="mt-2 max-h-48 space-y-1 overflow-y-auto">
              {documents.map((doc) => (
                <li key={doc.document_id}>
                  <button
                    onClick={() => onSelect(doc.document_id === activeDocumentId ? null : doc.document_id)}
                    className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs transition ${
                      activeDocumentId === doc.document_id
                        ? "bg-violet-500/10 text-violet-600 dark:text-violet-300"
                        : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
                    }`}
                  >
                    <FileText size={13} className="shrink-0" />
                    <span className="truncate">{doc.filename}</span>
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleForget(doc.document_id)
                      }}
                      className="ml-auto shrink-0 text-zinc-400 hover:text-rose-500"
                    >
                      <Trash2 size={13} />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
