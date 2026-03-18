import sys
import docx

def read_docx(file_path):
    out = []
    out.append(f"=== {file_path} ===")
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            if para.text.strip():
                out.append(para.text)
    except Exception as e:
        out.append(f"Error reading {file_path}: {e}")
    out.append("\n" + "="*40 + "\n")
    return "\n".join(out)

if __name__ == "__main__":
    text1 = read_docx("SYNAPSE_PRD.docx")
    text2 = read_docx("SYNAPSE_SystemDesign.docx")
    with open("docs_content_utf8.txt", "w", encoding="utf-8") as f:
        f.write(text1 + "\n" + text2)
