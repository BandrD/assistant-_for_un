from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("sample.pdf", pagesize=letter)
c.drawString(100, 750, "Экзаменационная сессия проходит с 10 по 20 июня 2025 года.")
c.save()
