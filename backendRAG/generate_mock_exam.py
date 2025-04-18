import json
import time
import openai
from dotenv import load_dotenv
import os

class Generator:
    """Class for generating HKDSE-style reading material using OpenAI."""

    def __init__(self):
        # Load API key
        load_dotenv()
        api_key=os.getenv("OPENAI_4o_KEY")
        self.client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint="https://jacky-m7czpwq5-eastus2.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21",
            api_version="2024-10-21"
        )
    
    def generateQuestionPrompt(self, question_type, selected_materials, reference_question, remark):
        remark = "\n\t".join(remark)
        match question_type:
            case "true_false_not_given":
                prompt = self.TFPrompt(selected_materials, reference_question, remark)
            case "short_question":
                prompt = self.shortQuestionPrompt(selected_materials, reference_question, remark)
            case "multiple_choice":
                prompt = self.MCPrompt(selected_materials, reference_question, remark)
            case "fill_in_the_blank":
                prompt = self.fillInBlankPrompt(selected_materials, reference_question, remark)
            case "matching":
                prompt = self.matchingPrompt(selected_materials, reference_question, remark)
            case "multi_short_question":
                prompt = self.multiShortQuestionPrompt(selected_materials, reference_question, remark)
            case _:
                raise ValueError(f"Unsupported question type: {question_type}")
        
        return prompt

    def readingPromt(self, topic, selected_materials, words_number, max_para, remark):
        remark = "\n\t".join(remark)
        prompt = f"""
        You are an expert in **HKDSE English reading paper creation**.  
        Your task is to generate a **new reading material** based on the given **HKDSE past paper reading text**.  

        ## **📌 Task Instructions:**
        - The new reading material should follow the given **topic:** **"{topic}"**.
        - It must **maintain a similar length, format, and structure** as the provided passage.
        - It must have at least **{words_number}** words.
        - It must contain at most {max_para} paragraphs. Ideally, it should match the number of paragraphs in the given reading text.
        - Do **not include any instructions or explanations in the output, only the generated reading material"".
        {remark}

        ## **📌 HKDSE past paper reading text:**
        {selected_materials}

        ## **📌 Output Format:**
        The generated reading material should follow this structure which is same as the given reading text:

        Title: [Generated Title]
        Subtitle: [Generated Subtitle]
        Content:  
        [Generated paragraphs and sections(if exist)]  
        """
        return prompt
    
    
    def MCPrompt(self, reading_material, reference, remark):
        prompt = f"""
        You are an expert in **HKDSE English Reading exam paper creation**.
        Your task is to generate ONE **multiple-choice question (MCQ)** based on the provided text paragraphs and taking reference from the Question Sample.
        The Question Sample is taken from the past paper in JSON format with all the related information.
        The provided text is a list of dictionaries. Each dictionary represents either:
            - a subtitle, in the format: {{"subtitle": text}}
            - a title, in the format: {{"title": text}}
            - a full paragraph, in the format: {{"para_id": paragraph number, "section": section name, "text": full paragraph text}}
        
        ## **📌 Provided Text Paragraphs:**
        {reading_material}

        ## **📌 Question Sample (Follow this style):**
        {json.dumps(reference, indent=4)}
        
        ## **📌 Task Instructions:**
        - The generated question should follow this JSON format:
        {{
          "question_type": "multiple_choice",
          "question_text": [Question related to the passage],
          "options": {{
            "A": [Option A],
            "B": [Option B],
            "C": [Option C],
            "D": [Option D]
          }},
          "answer": [Correct answer(s) (e.g., C)],
          "related_paragraphs": [{{Extract the content dictionary which the answer is derived from the provided text paragraphs}}]
        }}
        
        - **Note that the `related_paragraphs` field in the reference MCQs comes from a different text.**
        - **Use only information found in the provided text.**
        - **It is not necessary to use all the provided text paragraphs**
        - **Ensure that the generated question originates from a similar paragraph(s) area as stated in the Question Sample**
        - **Ensure the  difficulty level is similar to Question Sample.**
        - **If paragraph(s) is indicated in the Question Sample, it must have paragraph(s) indicated in the generated question text too.**
        {remark}
        

        ## **📌 Output Format:**  
        Return only a single JSON object. Do not include any explanations, comments, or markdown formatting.
        """
        return prompt
    
    def shortQuestionPrompt(self, reading_material, reference, remark):
        prompt = f"""
        You are an expert in **HKDSE English Reading exam paper creation**.
        Your task is to generate ONE **short question** based on the provided text paragraphs and taking reference from the short question sample.
        The short question sample is taken from the past paper in JSON format with all the related information.
        The provided text is a list of dictionaries. Each dictionary represents either:
            - a subtitle, in the format: {{"subtitle": text}}
            - a title, in the format: {{"title": text}}
            - a full paragraph, in the format: {{"para_id": paragraph number, "section": section name, "text": full paragraph text}}
        Notice that the answer(s) is stored in an array where each element is one of the possible answers, which means student answer either one is enough.
        It is not necessart to generate the same number of answers.
        In answer, you may see symbols like () and /:
            - () means the words inside the bracket can be neglected
            - / means the words are interchangable
        
        ## **📌 Provided Text Paragraphs:**
        {reading_material}

        ## **📌 Short Question Sample (Follow this style):**
        {json.dumps(reference, indent=4)}
        
        ## **📌 Task Instructions:**
        - The generated question should follow this JSON format which is same as the Short Question Sample:
        {{
          "question_type": "short_question",
          "question_text": [Question related to the passage],
          "answer": [Correct answer(s) (e.g., (a time) when people played video/technology games)],
          "related_paragraphs": [{{Extract the content dictionary which the answer is derived from the provided text paragraphs}}]
        }}
        
        - **Note that the "related_paragraphs" field in the Short Question sample comes from a different text.**
        - **Use only information found in the provided text.**
        - **It is not necessary to use all the provided text paragraphs**
        - **Ensure that the generated question originates from a similar paragraph(s) area as stated in the sample**
        - **Provide challenging but fair questions that match the HKDSE reading difficulty level.**
        - **If paragraph(s) is indicated in the Short Question Sample, it must have paragraph(s) indicated in the generated question text too.**
        {remark}
        

        ## **📌 Output Format:**  
        Return only a single JSON object. Do not include any explanations, comments, or markdown formatting.
        """
        return prompt
    
    def multiShortQuestionPrompt(self, reading_material, reference, remark): #quality need improve
        num_sub_questions = len(reference["sub_questions"])
        prompt = f"""
        You are an expert in **HKDSE English Reading exam paper creation**.
        Your task is to generate **mutiple short question** based on the provided text paragraphs and taking reference from the Question Sample.
        The Question Sample is taken from the past paper in JSON format with all the related information.
        The provided text is a list of dictionaries. Each dictionary represents either:
            - a subtitle, in the format: {{"subtitle": text}}
            - a title, in the format: {{"title": text}}
            - a full paragraph, in the format: {{"para_id": paragraph number, "section": section name, "text": full paragraph text}}
        "answer" is an array where each element is one of the possible answers, which means student answer either one is enough.
        In "answer", you may see symbols like () and /:
            - () means the words inside the bracket can be neglected
            - / means the words are interchangable

        ## 📌 Provided Text Paragraphs:
        {reading_material}


        ## 📌 Question Sample (Follow this structure):
        {json.dumps(reference, indent=4)}
        
        ## **📌 Task Instructions:**
        - The generated question should follow this JSON format which is same as the Short Question Sample:
        {{
        "question_type": "multi_short_question",
        "question_text": [Question related to the passage],
        "sub_questions": [
            {{
                "text": [The question],
                answer": [Correct answer]
            }}
        ],
        "related_paragraphs": [{{Extract the content dictionary which the answer is derived from the provided text paragraphs}}]
        }}
        
        - **Note that the `related_paragraphs` field in the Short Question sample comes from a different text.**
        - **Use only information found in the provided text.**
        - **It is not necessary to use all the provided text paragraphs**
        - **Ensure that the generated question originates from a similar paragraph(s) area as stated in the sample**
        - **Ensure the difficulty level and content complexity are similar to the sample.**
        - **If paragraph(s) is indicated in the Question Sample, it must have paragraph(s) indicated in the generated question text too.**
        - **Make sure your generated answers follow the same style (length, structure, tone) as those in the Question Sample.**
        - **The number of elements inside the "sub_questions" must be exactly {num_sub_questions}.**
        {remark}
        

        ## **📌 Output Format:**  
        Return only a single JSON object. Do not include any explanations, comments, or markdown formatting.
        """
        return prompt

    def TFPrompt(self, reading_material, reference, remark):
        prompt = f"""
        You are an expert in **HKDSE English Reading exam paper creation**.
        Your task is to generate **True False Not Given question** based on the provided text paragraphs and taking reference from the True False Not Given question sample.
        The True False Not Given question sample is taken from the past paper in JSON format with all the related information.
        The provided text is a list of dictionaries. Each dictionary represents either:
            - a subtitle, in the format: {{"subtitle": text}}
            - a title, in the format: {{"title": text}}
            - a full paragraph, in the format: {{"para_id": paragraph number, "section": section name, "text": full paragraph text}}
        
        ## **📌 Provided Text Paragraphs:**
        {reading_material}

        ## **📌 True False Not Given Question Sample (Follow this style):**
        {json.dumps(reference, indent=4)}
        
        ## **📌 Task Instructions:**
        - The generated question should follow this JSON format which is same as the True False Not Given Question Sample:
        {{
            "question_type": "true_false_not_given",
            "question_text": "[Decide whether the following statements are True, False, or Not Given based on paragraphs xxx]",
            "statements": [
                {{
                    "text": [The statement],
                    answer": [True/False/Not Given]
                }}
            ],
            "related_paragraphs": [{{Extract the content dictionary which the answer is derived from the provided text paragraphs}}]
        }}
        
        - **Note that the `related_paragraphs` field in the True False Not Given Sample comes from a different text.**
        - **Use only information found in the provided text.**
        - **It is not necessary to use all the provided text paragraphs**
        - **Ensure that the generated question originates from a similar paragraph(s) area as stated in the sample**
        - **Ensure the  difficulty level is similar to Question Sample.**
        {remark}
        

        ## **📌 Output Format:**  
        Return only a single JSON object. Do not include any explanations, comments, or markdown formatting.
        """
        return prompt
    
    def fillInBlankPrompt(self, reading_material, reference, remark):
        num_blanks = reference["text_for_fill"].count("___")
        prompt = f"""
        You are an expert in **HKDSE English Reading exam paper creation**.
        Your task is to generate **Fill In the Blank question** based on the provided text paragraphs and taking reference from the Fill In the Blank question sample.
        The question sample is taken from the past paper in JSON format with all the related information.
        The provided text is a list of dictionaries. Each dictionary represents either:
            - a subtitle, in the format: {{"subtitle": text}}
            - a title, in the format: {{"title": text}}
            - a full paragraph, in the format: {{"para_id": paragraph number, "section": section name, "text": full paragraph text}}
        In "text_for_fill", each "___" represents a blank that must be filled based on the instruction provided in "question_text" (e.g. Use ONE word to fill in each blank).
        The "answer" field is a list where each element corresponds to a blank in the text, based on its order of appearance (i.e. the first element matches the first blank, the second element matches the second blank, and so on)
        You may encounter the following symbols in "answer:
            - () means the words inside the bracket can be neglected
            - // means either word(s) is accepted as correct
        
        
        
        ## **📌 Provided Text Paragraphs:**
        {reading_material}

        ## **📌 Question Sample (Follow this style):**
        {json.dumps(reference, indent=4)}
        
        ## **📌 Task Instructions:**
        - The generated question should follow this JSON format which is same as the Question Sample:
        {{
            "question_type": "fill_in_the_blank",
            "question_text": "[Take reference from the Question Sample and state clearly how many words are allowed]",
            "text_for_fill": [Text with "___" for fill],
            "answer": [A list that store the answer of each blank in order],
            "related_paragraphs": [{{Extract the content dictionary which the answer is derived from the provided text paragraphs}}]
        }}
        
        - **Note that the `related_paragraphs` field in the Question Sample comes from a different text.**
        - **Use only information found in the provided text.**
        - **It is not necessary to use all the provided text paragraphs, but make sure the amount of content used is similar to the Question Sample**
        - **Ensure the  difficulty and complexity level is similar to Question Sample.**
        - **The number of blanks "___" in "text_for_fill" must be exactly {num_blanks}.**
        {remark}
        

        ## **📌 Output Format:**  
        Return only a single JSON object. Do not include any explanations, comments, or markdown formatting.
        """
        return prompt
    
    def matchingPrompt(self, reading_material, reference, remark): #modify this
        prompt = f"""
            You are an expert in **HKDSE English Reading exam paper creation**.
            Your task is to generate a **Matching-type question** based on the provided text paragraphs and by taking reference from the matching-type question sample.
            The question sample is taken from a past HKDSE paper and is provided in JSON format with all the related information.
            The provided text is a list of dictionaries. Each dictionary represents either:
                - a subtitle, in the format: {{"subtitle": text}}
                - a title, in the format: {{"title": text}}
                - a full paragraph, in the format: {{"para_id": paragraph number, "section": section name, "text": full paragraph text}}


            ## **📌 Provided Text Paragraphs:**
            {reading_material}

            ## **📌 Matching-Type Question Sample (Follow this style):**
            {json.dumps(reference, indent=4)}
            
            ## **📌 Task Instructions:**
            - The generated question should follow this JSON format which is the same as the Matching-Type Question Sample:
            {{
                "question_type": "matching",
                "question_text": [Question for student],
                "statement": [
                    {{
                        "text": [Item to be matched],
                        "answer": [Matching item]
                    }}
                ],
                "related_paragraphs": [{{Extract the content dictionary which the answer is derived from the provided text paragraphs}}]
            }}

            - **Note that the `related_paragraphs` field in the Question Sample comes from a different text.**
            - **Use only information found in the provided text.**
            - **It is not necessary to use all the provided text paragraphs, but make sure the amount of content used is similar to the Question Sample**
            - **Ensure the difficulty level and content complexity are similar to the sample.**
            {remark}

            ## **📌 Output Format:**
            Return only a single JSON object. Do not include any explanations, comments, or markdown formatting.
            """
            
        return prompt
    
    def generate(self,prompt):

        response = self.client.chat.completions.create(  # ✅ Updated API call
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an expert HKDSE exam paper generator."},
                    {"role": "user", "content": prompt}]
        )
        
        print("🔹 Prompt Tokens Used:", response.usage.prompt_tokens)
        print("🔹 Completion Tokens Used:", response.usage.completion_tokens)
        print("🔹 Total Tokens Used:", response.usage.total_tokens)

        return response.choices[0].message.content  # ✅ Corrected response format
    










# if __name__ == "__main__":
    
    # Example Usage
    # topic = "Teenagers'growth"
    # generator = Generator()
    # result = []
    
    
    # Generate Reading Materials
    # with open("PastPaper/2012/PartA/text1.txt", "r", encoding="utf-8") as file:
    #     reading_materials = file.read()
    # readingPrompt = generator.readingPromt(topic, reading_materials)
    # response = generator.generate(readingPrompt)
    # print(response)
    # with open("learning-intelligent/Results/PartA/text1.txt", "w", encoding="utf-8") as file:
    #     file.write(response)
        
    # convertTxtToJson("A",1)
    # convertTextJsonToPdf("A", 1)
    # convertQuestionJsonToPdf("A")
        
    # Generate Questions
    # with open("PastPaper/2012/PartA/text1.json", "r", encoding="utf-8") as file:
    #     reading_materials_json = json.load(file)
    # with open("PastPaper/2012/PartA/questions.json", "r", encoding="utf-8") as file:
    #     questions = json.load(file)
    # error_responses = []
    
    # for i in range(len(questions["questions"])):
    #     question = questions["questions"][i]
    #     question_type = question["question_type"]
    #     selected_materials = getParagraphs("Results/PartA/text1.json",question["related_paragraphs"], reading_materials_json["para_num"])
        
    #     # print(selected_materials)
        
    #     id = question.pop("id", None)
    #     mark = question.pop("mark", 1)
    #     remark = question.pop("remark", [])
    #     style = question.pop("style", None)
            
    #     prompt = generator.generateQuestionPrompt(question_type,selected_materials, question, list(remark))
        
    #     for i in range(3):
    #         response_str = generator.generate(prompt)
    #         try:
    #             response = json.loads(response_str)
    #             break
    #         except:
    #             error_responses.append({
    #                 "attempt": i + 1,
    #                 "raw_response": response_str,
    #                 "prompt": prompt
    #             })
    #             if i == 2:
    #                 remark.append("- **Ensure the output is a single JSON object**")
    #                 prompt = generator.generateQuestionPrompt(question_type,selected_materials, question, list(remark))
    #             time.sleep(1)
                
    #     print(response)
    #     if response is not None:
    #         response["id"] = id
    #         response["mark"] = mark
    #         response["style"] = style
    #         result.append(response)
        
    # print(result)
    
    # if error_responses:
    #     print("🚨 Has no json generated!!")
    #     print(error_responses)
        
    
    # with open("Results/PartA/question.json", "w", encoding="utf-8") as file:
    #     json.dump(result, file, indent=4, ensure_ascii=False)
    
    # convertQuestionJsonToPdf("A")