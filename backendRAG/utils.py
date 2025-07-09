import json, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def clean_text(text):
    return text.replace("’", "'").replace("–", "-").replace("‘","'")

def convertTxtToJson(part,text_id, uid):
    read_file_path = f"Results/{part}/{uid}_text{text_id}.txt"
    write_file_path = f"Results/{part}/{uid}_text{text_id}.json"
    # print(read_file_path)
    with open (read_file_path, 'r', encoding="utf-8") as file:
        lines = file.readlines()
    
    text_data = {
        "text_id": text_id,
        "title":"",
        "subtitle":"",
        "content":[]
    }
    current_section = ""
    paragraphs = []
    paragraph_id = 1
    
    for line in lines:
        line = line.strip()
        
        if not line or line.startswith("```") or line.startswith("Content:"):  
            continue 
        elif line.startswith("Title:"):
            text_data["title"] = clean_text(line.replace("Title:", "").strip())
        elif line.startswith("Subtitle:"):
            text_data["subtitle"] = clean_text(line.replace("Subtitle:", "").strip())
        elif "Section:" in line:
            # Flush buffer to paragraphs before changing section  
            for p in paragraphs:  
                if p:  
                    text_data["content"].append({  
                        "para_id": paragraph_id,  
                        "section": current_section,  
                        "text": clean_text(p)  
                    })  
                    paragraph_id += 1  
            paragraphs = []  
            match = re.search(r"Section:\s*((\([A-Za-z0-9]+\))?\s*[A-Za-z0-9\s]*)", line)
            if match:
                raw_section = match.group(1)
                cleaned_section = re.sub(r"[^\w()\s]+$", "", raw_section).strip()
                current_section = clean_text(cleaned_section)

        else:  
            paragraphs.append(line)  

    # Save last section
    for p in paragraphs:  
        if p: 
            text_data["content"].append({  
                "para_id": paragraph_id,  
                "section": current_section,  
                "text": clean_text(p)  
            })  
            paragraph_id += 1  

    # Save to JSON file
    with open(write_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(text_data, json_file, indent=4, ensure_ascii=False)
    
    return

def countParaNum(response):
    lines = response.split("\n")
    para_num = 0
    for line in lines:
        line = line.strip()

        # Skip empty lines and metadata
        if (
            not line or
            line.startswith("```") or
            line.startswith("Content:") or
            line.startswith("Title:") or
            line.startswith("Subtitle:") or
            "Section:" in line
        ):
            continue

        # Count as a valid paragraph
        para_num += 1

    return para_num
    
def getParagraphs(file_path, related_paragraphs, given_text_length):
    """
    Reads a JSON file and extracts specific paragraphs by index.

    :param file_path: Path to the JSON file.
    :param paragraph_index: A list of paragraph numbers to extract (1-based).
    :return: A dictionary with paragraph numbers as keys and paragraph text as values.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    result = []
    paragraph_ids = set()
    
    # Step 1: Create paragraph lookup map
    paragraph_map = {p["para_id"]: p for p in data.get("content", [])}
    generated_text_length = len(paragraph_map)
    # Step 2: Identify which elements to include
    for entry in related_paragraphs:
        if "para_id" in entry:
            if (entry["para_id"] > generated_text_length):
                difference = given_text_length - entry["para_id"]
                pid = generated_text_length - difference
            else:
                pid = entry["para_id"]
            paragraph_ids.add(pid)
        if "title" in entry:
            result.append({ "title": data.get("title", "") })
        if "subtitle" in entry:
            result.append({ "subtitle": data.get("subtitle", "") })
    
    # Step 3: Include neighbors (pid - 1, pid, pid + 1)
    neighbor_ids = set()
    for pid in paragraph_ids:
        neighbor_ids.update({pid - 1, pid, pid + 1})

    # Step 4: Add paragraph objects in order
    for pid in sorted(neighbor_ids):
        if pid in paragraph_map:
            result.append(paragraph_map[pid])
            
    return result

def convertTextJsonToPdf(part,text_id, uid):
    json_path = f"Results/{part}/{uid}_text{text_id}.json"
    pdf_path = f"Results/{part}/{uid}_text{text_id}.pdf"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Setup PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    # Define custom styles
    title_style = styles['Title']
    subtitle_style = styles['Heading2']
    paragraph_style = styles['BodyText']
    section_style = ParagraphStyle(name='SectionHeader',
                                   parent=styles['Heading3'],
                                   spaceBefore=12, spaceAfter=6,
                                   fontSize=12, textColor="darkblue")

    # Add title and subtitle
    story.append(Paragraph(data["title"], title_style))
    story.append(Spacer(1, 12))
    subtitle_lines = data["subtitle"].split("\n")
    for line in subtitle_lines:
        story.append(Paragraph(line, subtitle_style))
    story.append(Spacer(1, 24))

        # Track sections that have already been added
    seen_sections = set()

    # Add content
    for para in data.get("content", []):
        section = para.get("section", "").strip()
        text = para.get("text", "")

        # Only show section title the first time
        if section and section not in seen_sections:
            story.append(Paragraph(section, section_style))
            story.append(Spacer(1, 6))
            seen_sections.add(section)

        # Add paragraph text
        story.append(Paragraph(text, paragraph_style))
        story.append(Spacer(1, 12))

    # Build PDF
    doc.build(story)
    return

def renderQestionByType(q, idx, styles):
    elements = []
    q_type = q.get("question_type", "short_question")
    q_text = q.get("question_text", "No question text.")
    q_style = q.get("style", [])

    # Add question number and text
    elements.append(Paragraph(f"{idx}. {q_text}", styles['question']))
    elements.append(Spacer(1, 6))

    match q_type:
        case "multiple_choice":
            options = q.get("options", {})

            keys = list(options.keys())

            # Step 1: Create the bubble grid (2 rows — label and circle)
            label_row = [Paragraph(f"<b>{k}</b>", styles["option"]) for k in options]
            circle_row = [Paragraph("○", styles["option"]) for _ in options]

            bubble_table = Table([label_row, circle_row], colWidths=[20] * len(options))
            bubble_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ]))

            # Step 2: Create the main 4x2 table rows
            # 1 inner list 1 row, 1 element 1 cell
            option_rows = [
                [Paragraph(f"<b>{keys[0]}.</b> {options[keys[0]]}", styles['option']), ''],
                [Paragraph(f"<b>{keys[1]}.</b> {options[keys[1]]}", styles['option']), ''],
                
                # C and D share the bubble_table on the right
                [Paragraph(f"<b>{keys[2]}.</b> {options[keys[2]]}", styles['option']), bubble_table],
                [Paragraph(f"<b>{keys[3]}.</b> {options[keys[3]]}", styles['option']), '']
            ]

            # Step 3: Define the table and apply row span
            main_table = Table(option_rows, colWidths=[350, 100])
            main_table.setStyle(TableStyle([
                ("SPAN", (1, 2), (1, 3)),  # all row/col starts with 0 i.e. (1,2) is second column third row
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0), # ("COMMAND", (col_start, row_start), (col_end, row_end), value)
                ("RIGHTPADDING", (0, 0), (-1, -1), 2), # (0,0), (-1,-1) = Entire Table
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))

            # Step 4: Indent the whole thing to align with the question
            indented_table = Table([[main_table]]) # | [main_table with options + bubbles] |
            indented_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))

            elements.append(indented_table)
            
        case "multi_choice":
            options = q.get("options", {})

            for key, value in options.items():
                option_text = f"○ {key}. {value}"
                elements.append(Paragraph(option_text, styles['option']))
                elements.append(Spacer(1, 4))

        case "short_question":
            # Add 2 lines for answer
            line_count = 1  # default

            for style in q_style:
                if style.endswith("_line"):
                    if style.split("_")[0].isdigit():
                        line_count = int(style.split("_")[0])
                        for _ in range(line_count):
                            elements.append(Spacer(1, 4))
                            elements.append(Paragraph("______________________________________________________________________", styles['answer']))
                    else:
                        elements.append(Spacer(1, 4))
                        elements.append(Paragraph("__________________________", styles['answer']))
                    


        case "multi_short_question":
            for sub in q.get("sub_questions", []):
                elements.append(Paragraph(f"{sub['text']}: ", styles['sub']))
                elements.append(Paragraph("______________________________________________________________________", styles['sub']))

        case "matching":
            # Render as table with two columns
            data = []
            subquestion = q.get("statements",[])
            
            # Row 0: Header
            data.append([
                Paragraph("<b>Expressions</b>", styles['header']),
                Paragraph("<b>Answer</b>", styles['header']),
            ])
            
            # Row 1..n: Statements
            for i in range(len(subquestion)):
                statement_text = subquestion[i].get('text','')
                data.append([
                    Paragraph(statement_text, styles['sub'])
                ])

            matching_table = Table(data, colWidths=[300, 100])
            matching_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]))
            elements.append(Spacer(1, 6))
            elements.append(matching_table)

        case "true_false_not_given":
            # Build the rows for the table
            data = []
            subquestion = q.get("statements",[])
            
            # Row 0: Header
            data.append([
                Paragraph("<b>Statements</b>", styles['header']),
                Paragraph("<b>T</b>", styles['header']),
                Paragraph("<b>F</b>", styles['header']),
                Paragraph("<b>NG</b>", styles['header'])
            ])

            # Row 1..n: Statements + circles
            for i in range(len(subquestion)):
                statement_text = f"{i+1}) {subquestion[i].get('text','')}"
                data.append([
                    Paragraph(statement_text, styles['sub']),
                    Paragraph("◯", styles['option']),
                    Paragraph("◯", styles['option']),
                    Paragraph("◯", styles['option'])
                ])

            # Create the table
            tfng_table = Table(data, colWidths=[320, 30, 30, 30])
            tfng_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER')
            ]))
            
            elements.append(Spacer(1, 6))
            elements.append(tfng_table)

        case "fill_in_the_blank":
            fill_text = q.get("text_for_fill", "")
            formatted = fill_text.replace("___", "_________").replace("_____", "_________").replace("\n", "<br/>")
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(formatted, styles['option']))

        case _:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("Answer: ____________________________", styles['answer']))

    # Add bottom spacing after each question
    elements.append(Spacer(1, 16))
    return elements

def renderAnswerByType(q, idx, styles): 
    elements = []
    q_type = q.get("question_type", "")

    match q_type:
        case "multiple_choice":
            answer = q.get('answer')[0]
            elements.append(Paragraph(f"{idx}. {answer}", styles['answer']))
            
        case "multi_choice":
            answers = ", ".join(q.get("answer", []))
            elements.append(Paragraph(f"{idx}. {answers}", styles['answer']))

        case "short_question":
            answers = "//".join(q.get("answer", []))
            elements.append(Paragraph(f"{idx}. {answers}", styles['answer']))


        case "multi_short_question":
            elements.append(Paragraph(f"{idx}.", styles['answer']))
            for question in q.get("sub_questions", []):
                answers = "//".join(question["answer"])
                elements.append(Paragraph(f"{question['text']}: {answers}", styles['answer']))

        case "matching":
            elements.append(Paragraph(f"{idx}.", styles['answer']))
            for question in q.get("statements", []):
                answers = question["answer"]
                elements.append(Paragraph(f"{question['text']}: {answers}", styles['answer']))

        case "true_false_not_given":
            elements.append(Paragraph(f"{idx}.", styles['answer']))
            for question in q.get("statements", []):
                answers = question["answer"]
                elements.append(Paragraph(f"{answers}", styles['answer']))

        case "fill_in_the_blank":
            elements.append(Paragraph(f"{idx}.", styles['answer']))
            
            fill_text = q.get("text_for_fill", "")
            answers = q.get("answer", [])
            # Replace each blank "___" with an underlined space + answer
            parts = fill_text.split("___")
            filled_text = ""

            for i in range(len(parts)):
                filled_text += parts[i]
                if i < len(answers):
                    filled_text += f"<u>{answers[i]}</u>"  # underlined answer

            elements.append(Paragraph(filled_text.replace("\n", "<br/>"), styles['option']))

        case _:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("Answer: ____________________________", styles['answer']))
            
    elements.append(Spacer(1, 16))
    return elements
    
def convertQuestionJsonToPdf(part, uid):
    json_path = f"Results/{part}/{uid}_questions.json"
    question_pdf_path = f"Results/{part}/{uid}_questions.pdf"
    answer_pdf_path = f"Results/{part}/{uid}answers.pdf"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # questions = data.get("questions", [])
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'fonts/DejaVuSans.ttf'))
    
    if part == "PartA":
        box_data = [
            ["A"],
            ["COMPULSORY"]
        ]
    elif part == "PartB1":
        box_data = [
            ["B1"],
            ["EASY SECTION"]
        ]
    else:
        box_data = [
            ["B2"],
            ["DIFFICULT SECTION"]
        ]

    box = Table(box_data, colWidths=[90], rowHeights=[50, 20])

    # Apply styles
    box.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center horizontally
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Center vertically
        ('FONTSIZE', (0, 0), (0, 0), 32),  
        ('FONTSIZE', (0, 1), (0, 1), 8), 
        ('BOTTOMPADDING', (0, 0), (0, 0), 0),
        ('TOPPADDING', (0, 0), (0, 0), -5),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),  # Black border
    ]))
    
    base_styles = getSampleStyleSheet()
    styles = {
        'title': base_styles['Title'],
        'question': ParagraphStyle('Question', parent=base_styles['BodyText'], fontSize=11, spaceAfter=6, leading=14),
        'header': ParagraphStyle('Header', parent=base_styles['BodyText'], fontSize=10, leading=12, alignment=0),
        'option': ParagraphStyle('Option', parent=base_styles['BodyText'], fontSize=10, fontName='DejaVuSans'),
        'answer': ParagraphStyle('Answer', parent=base_styles['BodyText'], leftIndent=20, fontSize=10),
        'sub': ParagraphStyle('Sub', parent=base_styles['BodyText'], fontSize=10)
    }
    
    question_story = [box, Spacer(1, 24)]
    answer_story = [Paragraph(f"{part} - Answer Key", styles['title']), Spacer(1, 24)]
    for question in data:
        qid = question.get("id", "0_textx").split('_')[0]
        question_story.extend(renderQestionByType(question, qid, styles))
        answer_story.extend(renderAnswerByType(question, qid, styles))
    
    question_doc = SimpleDocTemplate(question_pdf_path, pagesize=A4,
                                     rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    question_doc.build(question_story)
    

    answer_doc = SimpleDocTemplate(answer_pdf_path, pagesize=A4,
                            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    answer_doc.build(answer_story)

# convertQuestionJsonToPdf("PartB2", "1")
# f"PastPaper/2012/{part}/questions.json"
# f"Results/{part}/{uid}_questions.json"
# f"Results/{part}/{uid}_answers.pdf"