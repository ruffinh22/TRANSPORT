import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import * as XLSX from 'xlsx'

export const exportService = {
  /**
   * Export un élément HTML en PDF
   */
  exportToPDF: async (
    elementId: string,
    fileName: string = 'export.pdf',
    orientation: 'portrait' | 'landscape' = 'landscape'
  ) => {
    try {
      const element = document.getElementById(elementId)
      if (!element) {
        throw new Error(`Élément avec l'ID "${elementId}" non trouvé`)
      }

      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#ffffff',
      })

      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF({
        orientation,
        unit: 'mm',
        format: 'a4',
      })

      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = pdf.internal.pageSize.getHeight()
      const imgWidth = pdfWidth - 20
      const imgHeight = (canvas.height * imgWidth) / canvas.width

      let heightLeft = imgHeight
      let position = 10

      pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
      heightLeft -= pdfHeight - 20

      while (heightLeft >= 0) {
        position = heightLeft - imgHeight + 10
        pdf.addPage()
        pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight)
        heightLeft -= pdfHeight - 20
      }

      pdf.save(fileName)
      return { success: true, message: `PDF exporté: ${fileName}` }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  },

  /**
   * Export un tableau en CSV
   */
  exportToCSV: (
    data: any[],
    fileName: string = 'export.csv',
    columns?: string[]
  ) => {
    try {
      if (data.length === 0) {
        throw new Error('Aucune donnée à exporter')
      }

      // Déterminer les colonnes
      const keys = columns || Object.keys(data[0])

      // Créer l'en-tête CSV
      const header = keys.join(',')

      // Créer les lignes CSV
      const rows = data.map((item) =>
        keys
          .map((key) => {
            const value = item[key]
            if (value === null || value === undefined) return ''
            if (typeof value === 'string' && value.includes(',')) {
              return `"${value}"`
            }
            return value
          })
          .join(',')
      )

      const csv = [header, ...rows].join('\n')

      // Télécharger le fichier
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = fileName
      link.click()

      return { success: true, message: `CSV exporté: ${fileName}` }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  },

  /**
   * Export un tableau en Excel
   */
  exportToExcel: (
    data: any[],
    fileName: string = 'export.xlsx',
    sheetName: string = 'Feuille1',
    columns?: string[]
  ) => {
    try {
      if (data.length === 0) {
        throw new Error('Aucune donnée à exporter')
      }

      // Préparer les données
      const keys = columns || Object.keys(data[0])
      const formattedData = data.map((item) => {
        const row: any = {}
        keys.forEach((key) => {
          row[key] = item[key] || ''
        })
        return row
      })

      // Créer le workbook
      const ws = XLSX.utils.json_to_sheet(formattedData)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, sheetName)

      // Style basique (largeur des colonnes)
      const wscols = keys.map(() => ({ wch: 15 }))
      ws['!cols'] = wscols

      // Télécharger le fichier
      XLSX.writeFile(wb, fileName)

      return { success: true, message: `Excel exporté: ${fileName}` }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  },

  /**
   * Export un rapport complet (PDF avec logo et en-têtes)
   */
  exportReportToPDF: async (
    title: string,
    subtitle: string,
    content: string,
    fileName: string = 'rapport.pdf'
  ) => {
    try {
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      })

      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      let yPosition = 20

      // En-tête gouvernemental
      pdf.setFontSize(10)
      pdf.setTextColor(206, 17, 38) // Rouge TKF
      pdf.text('République du Burkina Faso', pageWidth / 2, yPosition, { align: 'center' })
      yPosition += 5
      pdf.setFontSize(9)
      pdf.text('Ministère des Transports et de la Mobilité Urbaine', pageWidth / 2, yPosition, { align: 'center' })
      yPosition += 5
      pdf.text('Unité - Progrès - Travail', pageWidth / 2, yPosition, { align: 'center' })
      yPosition += 10

      // Ligne de séparation
      pdf.setDrawColor(206, 17, 38)
      pdf.line(10, yPosition, pageWidth - 10, yPosition)
      yPosition += 8

      // Titre du rapport
      pdf.setFontSize(16)
      pdf.setTextColor(0, 122, 94) // Vert TKF
      pdf.text(title, pageWidth / 2, yPosition, { align: 'center' })
      yPosition += 10

      // Sous-titre
      pdf.setFontSize(11)
      pdf.setTextColor(80, 80, 80)
      pdf.text(subtitle, pageWidth / 2, yPosition, { align: 'center' })
      yPosition += 12

      // Contenu
      pdf.setFontSize(10)
      pdf.setTextColor(0, 0, 0)
      const lines = pdf.splitTextToSize(content, pageWidth - 20)
      pdf.text(lines, 10, yPosition)

      // Pied de page
      pdf.setFontSize(8)
      pdf.setTextColor(150, 150, 150)
      pdf.text(
        `Généré le ${new Date().toLocaleString('fr-FR')}`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      )

      pdf.save(fileName)
      return { success: true, message: `Rapport PDF exporté: ${fileName}` }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  },

  /**
   * Imprimer un élément HTML
   */
  printElement: (elementId: string) => {
    try {
      const element = document.getElementById(elementId)
      if (!element) {
        throw new Error(`Élément avec l'ID "${elementId}" non trouvé`)
      }

      const printWindow = window.open('', '', 'height=400,width=600')
      if (printWindow) {
        printWindow.document.write(element.outerHTML)
        printWindow.document.close()
        printWindow.print()
      }

      return { success: true, message: 'Impression lancée' }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  },

  /**
   * Générer un rapport statistique en JSON
   */
  generateStatisticsReport: (data: any, fileName: string = 'statistiques.json') => {
    try {
      const reportData = {
        generatedAt: new Date().toISOString(),
        generatedBy: 'TKF - Système de Gestion du Transport',
        data,
      }

      const blob = new Blob([JSON.stringify(reportData, null, 2)], {
        type: 'application/json',
      })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = fileName
      link.click()

      return { success: true, message: `Rapport JSON exporté: ${fileName}` }
    } catch (error) {
      return { success: false, error: String(error) }
    }
  },
}
