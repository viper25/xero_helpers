import math
import spacy

# Load the small English model from spaCy
nlp = spacy.load("en_core_web_sm")

layout_config = {
        "Text": {"linesPerSlide": 9, "charactersPerLine": 56},
        "TextAndImage": {"linesPerSlide": 9, "charactersPerLine": 32}
    }
def get_layout_config(layout_type):
    global layout_config
    return layout_config[layout_type]["linesPerSlide"] , layout_config[layout_type]["charactersPerLine"]

def get_effective_lines(text, layout_type):    
    lines_per_slide, characters_per_line = get_layout_config(layout_type)
    paragraphs = text.rstrip().split("\n")
    number_of_lines = sum([math.ceil((len(paragraph)) / characters_per_line) for paragraph in paragraphs])    
    # Increment number_of_lines by 1 for each empty paragraph
    number_of_lines += paragraphs.count('')
    return number_of_lines

# manual way. later use nlp
def split_paragraph(text, required_lines, layout_type):
    lines_per_slide, characters_per_line = get_layout_config(layout_type)
    required_characters = required_lines * characters_per_line
    try:
        sentences = text.rstrip().split(".")
        part1 = []
        current_characters = 0
        while len(sentences) > 0:        
            sentence_length = len(sentences[0]) + 1  # +1 for full stop
            if current_characters + sentence_length <= required_characters:
                part1.append(sentences.pop(0))
                current_characters += sentence_length
            else:
                break

        part1 = ".".join(part1)
        if not part1.rstrip().endswith("."):
            part1 += "."

        part2 = ".".join(sentences) # join remaining in sentences
        return part1, part2
    except Exception as e:
        print(f"Error in split_paragraph: {e}")
        raise Exception(f"Error in split_paragraph: {e}")

# using nlp 
def split_paragraph_into_sentences(paragraph: str) -> list[str]:
    # Process the text using the model
    doc = nlp(paragraph)
    # Extract sentences based on the parsing
    sentences = [sent.text.strip() for sent in doc.sents]
    return sentences

# Example usage
def split_paragraph_into_two(text, required_lines, layout_type):
    lines_per_slide, characters_per_line = get_layout_config(layout_type)
    required_characters = required_lines * characters_per_line
    try:
        sentences = split_paragraph_into_sentences(text)
        part1 = []
        current_characters = 0
        while len(sentences) > 0:        
            sentence_length = len(sentences[0]) + 1  # +1 for full stop
            if current_characters + sentence_length <= required_characters:
                part1.append(sentences.pop(0))
                current_characters += sentence_length
            else:
                break

        part1 = ' '.join(part1).strip()
        part2 = " ".join(sentences) # join remaining in sentences
        return part1, part2
    except Exception as e:
        print(f"Error in split_paragraph: {e}")
        raise Exception(f"Error in split_paragraph: {e}")

def split_text_into_slides(text, title, layout_type):
    chunks = text.split("\n")
    lines_per_slide, characters_per_line = get_layout_config(layout_type)
    # Create an array with text and effective number of lines for each chunk. effective_lines = math.ceil(line_length / characters_per_line)
    chunks_with_effective_lines = []
    slide_text_chunks = []
    line_counter = 0
    first_slide = True
    try:
        while len(chunks) > 0:
            chunk = chunks.pop(0)
            effective_lines = get_effective_lines(chunk,layout_type)
            if line_counter + effective_lines <= lines_per_slide:
                slide_text_chunks.append(chunk)
                line_counter += effective_lines
            else:
                # split the chunk into two parts. first part will be added to previous slide and second part will be added to next slide.
                part1, part2 = split_paragraph_into_two(chunk, lines_per_slide - line_counter, layout_type) # using nlp
                # part1, part2 = split_paragraph(chunk, lines_per_slide - line_counter, layout_type) # old way
                slide_text_chunks.append(part1)
                line_counter = lines_per_slide
                if part2:
                    # add it back to beginning of chunks
                    chunks.insert(0, part2)
            if line_counter >= lines_per_slide or len(chunks) == 0:
                # add slide_text to chunks_with_effective_lines
                slide_text = "\n".join(slide_text_chunks)
                title_new = title if first_slide else title + " (contd.)"
                chunks_with_effective_lines.append({"text": slide_text, "title": title_new, "layout": layout_type})
                slide_text_chunks = []
                line_counter = 0
                first_slide = False
                # change layout type to Text if it is not text. To ensure that 2nd slide onwards uses Text layout.
                if layout_type != "Text":
                    layout_type = "Text"
                    lines_per_slide, characters_per_line = get_layout_config(layout_type)
    except Exception as e:
        print(f"Error in split_text_into_slides: {e}")
        raise Exception(f"Error in split_text_into_slides: {e}")

    return chunks_with_effective_lines