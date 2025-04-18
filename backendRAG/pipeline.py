import json, os, time, copy, uuid
from utils import getParagraphs, convertTxtToJson, convertTextJsonToPdf, convertQuestionJsonToPdf, countParaNum
from job_store_redis import job_store
from generate_mock_exam import Generator
from config import MAX_READING_ATTEMPT,MAX_QUESTION_ATTEMPT, MAX_EXTRA_PARAGRAPH, MAX_LESS_PARAGRAPH, MIN_WORDS_DIFFERENT


def generateReadingMaterials(generator: Generator, topic, year, part, text_id, uid):
    remark = []
    read_path = f"PastPaper/{year}/{part}/text{text_id}.txt"
    read_path_json = f"PastPaper/{year}/{part}/text{text_id}.json"
    write_path = f"Results/{part}/{uid}_text{text_id}.txt"
    with open(read_path, "r", encoding="utf-8") as file:
        reading_materials = file.read()
    with open(read_path_json, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)  
        words_number = data["words_num"] - MIN_WORDS_DIFFERENT
        max_para = data["content"][-1]["para_id"] + MAX_EXTRA_PARAGRAPH
        # min_para = data["content"][-1]["para_id"] - MAX_LESS_PARAGRAPH
    
    readingPrompt = generator.readingPromt(topic, reading_materials, words_number, max_para, remark)
    for i in range(MAX_READING_ATTEMPT):
        response = generator.generate(readingPrompt)
        words_count = len(response.split())
        para_num = countParaNum(response)
        if words_count >= words_number and para_num <= max_para:
            break
        print("Words Count:", words_count)
        print("Paragraphs Number", para_num)
        time.sleep(1)
        if i == 2:
            remark.append(f"- **Please ensure the generated text contains at least {words_number} words and at most {max_para} paragraphs.**")
    # print(response)
    with open(write_path, "x", encoding="utf-8") as file:
        file.write(response)

def generateQuestions(generator: Generator, year, part, result: list, error: list, uid: uuid):
    with open(f"PastPaper/{year}/{part}/questions.json", "r", encoding="utf-8") as file:
        questions = json.load(file)
    
    # loop through every question and generate then one by one
    for q in range(len(questions["questions"])):
        if q > 6:
            break
        
        # extract data
        question = copy.deepcopy(questions["questions"][q])
        question_type = question["question_type"]
        print(q)
        print(question)
        print(questions["questions"][q-1])
        if q == 0 or question["id"][-1] != questions["questions"][q-1]["id"][-1]:
            text_id = question["id"][-1]
            with open(f"PastPaper/{year}/{part}/text{text_id}.json", "r", encoding="utf-8") as file:
                reading_materials_json = json.load(file)
        selected_materials = getParagraphs(f"Results/{part}/{uid}_text{text_id}.json",question["related_paragraphs"], reading_materials_json["content"][-1]["para_id"])
        
        # Take out the unuse materials to reduce the input complexity
        id = question.pop("id", None)
        mark = question.pop("mark", 1)
        remark = question.pop("remark", [])
        style = question.pop("style", None)
        
        # generate prompt
        prompt = generator.generateQuestionPrompt(question_type,selected_materials, question, list(remark)) # make a remark copy incase modify it
        
        # generate questions
        for i in range(MAX_QUESTION_ATTEMPT):
            response_str = generator.generate(prompt)
            try:
                response = json.loads(response_str)
                break
            except:
                response = None
                error.append({
                    "attempt": i + 1,
                    "raw_response": response_str,
                    "prompt": prompt
                })
                if i == 2:
                    remark.append("- **Ensure the output is a single JSON object**")
                    prompt = generator.generateQuestionPrompt(question_type,selected_materials, question, list(remark))
                time.sleep(1)
                
        # print(response)
        if response is not None:
            response["id"] = id
            response["mark"] = mark
            response["style"] = style
            result.append(response)
    
    with open(f"Results/{part}/{uid}_questions.json", "x", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)
    # return True
        
def run_generation_pipeline(topic: str, uid):
    # Example Usage
    print(topic)
    generator = Generator()
    result = []
    generation_error = []
    year = 2012
    
    # extract the corresponding past paper and feed it to AI 
    # Generate reading materials
    base_path = f"PastPaper/{year}"
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.startswith("text") and file.endswith(".txt"):  # 🔍 Only files starting with "text"
                part_name = os.path.relpath(root, base_path)  # 💡 Get 'PartA', 'PartB1', etc.
                text_id = file[-5]
                job_store.update_job(uid,"status",f"Generating {part_name} text{text_id}")
                generateReadingMaterials(generator, topic, year, part_name, text_id, uid)
                convertTxtToJson(part_name,text_id, uid)
                convertTextJsonToPdf(part_name, text_id, uid)
                
    # Generate questions
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file == "questions.json": 
                part_name = os.path.relpath(root, base_path)  # 💡 Get 'PartA', 'PartB1', etc.
                if part_name != "PartA":
                    continue
                job_store.update_job(uid,"status",f"Generating {part_name} questions.")
                generateQuestions(generator, year, part_name, result, generation_error, uid)
                convertQuestionJsonToPdf(part_name, uid)
    
    with open(f"Results/ErrorLog/{uid}_generationError.json", "x", encoding="utf-8") as file:
        json.dump(generation_error, file, indent=4, ensure_ascii=False)
        
    job_store.update_job(uid,"status","Done")
    
    # return {
    #     "success": True,
    #     "uuid": uid,
    #     "generated_count": len(result),
    #     "errors": generation_error
    # }