import * as pdfjsLib from 'pdfjs-dist';

// Set the worker source
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

class PDFProcessor {
  async extractTextFromPDF(file) {
    try {
      // Read the file as ArrayBuffer
      const arrayBuffer = await file.arrayBuffer();
      
      // Load the PDF document
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
      const pdf = await loadingTask.promise;
      
      let fullText = '';
      
      // Extract text from each page
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items.map(item => item.str).join(' ');
        fullText += pageText + '\n';
      }
      
      console.log('Extracted PDF Text:', fullText);
      return fullText;
      
    } catch (error) {
      console.error('Error extracting text from PDF:', error);
      throw error;
    }
  }

  parseCertificateData(text) {
    const data = {
      studentName: '',
      studentId: '',
      institution: '',
      issueDate: '',
      certificateNumber: '',
      subjects: []
    };

    // Common patterns in Lesotho LGCSE certificates
    const patterns = {
      // Student name patterns
      studentName: [
        /(?:Name|Student Name|Candidate)[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/i,
        /This (?:certifies|is to certify) that[:\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/i,
        /([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s+\(Candidate\))/i,
        /(?:Thabelo|Mosothoane|John|Jane|Thabo|Mokoena|Smith|Doe)/i
      ],
      
      // Student/ID number
      studentId: [
        /(?:Student|Candidate|Index)\s*(?:ID|Number)[:\s]*([A-Z0-9-]+)/i,
        /Centre\s*Number[:\s]*([A-Z0-9-]+)/i,
        /(\d{4,10})/i,
        /L\d{4}\/\d+/i
      ],
      
      // Institution
      institution: [
        /(?:Institution|School|Centre)[:\s]*([A-Za-z\s&]+)/i,
        /([A-Za-z\s]+(?:High School|Secondary School|College|Academy|ECOL))/i,
        /Examination Council of Lesotho/i
      ],
      
      // Date
      issueDate: [
        /(?:Issue Date|Date of Issue|Issued On)[:\s]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})/i,
        /(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})/i
      ],
      
      // Certificate number
      certificateNumber: [
        /(?:Certificate|Cert)\s*(?:No|Number)[:\s]*([A-Z0-9-]+)/i,
        /([A-Z]{2,5}\d{4,10})/i
      ]
    };

    // Apply patterns
    Object.entries(patterns).forEach(([field, patternList]) => {
      for (const pattern of patternList) {
        const match = text.match(pattern);
        if (match && match[1]) {
          data[field] = match[1].trim();
          break;
        }
      }
    });

    // Extract subjects (look for subject lines)
    const lines = text.split('\n');
    const subjectKeywords = ['Mathematics', 'English', 'Science', 'Biology', 'Chemistry', 'Physics', 
                             'Sesotho', 'History', 'Geography', 'Economics', 'Accounting', 'Commerce',
                             'Agriculture', 'Religious Education', 'Development Studies'];
    
    lines.forEach(line => {
      const matchedSubject = subjectKeywords.find(subject => 
        line.toLowerCase().includes(subject.toLowerCase())
      );
      if (matchedSubject) {
        // Try to extract grade
        const gradeMatch = line.match(/([A-F][0-9]?|[1-7])/);
        if (gradeMatch) {
          data.subjects.push({
            name: matchedSubject,
            grade: gradeMatch[1]
          });
        }
      }
    });

    return data;
  }

  async processCertificate(file) {
    try {
      // Extract text from PDF
      const extractedText = await this.extractTextFromPDF(file);
      
      // Parse the extracted text
      const parsedData = this.parseCertificateData(extractedText);
      
      return {
        success: true,
        data: parsedData,
        rawText: extractedText.substring(0, 500) // First 500 chars for preview
      };
    } catch (error) {
      console.error('PDF Processing Error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

export default new PDFProcessor();
