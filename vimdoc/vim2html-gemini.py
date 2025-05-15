#!/usr/bin/env python3

# converts vim documentation to simple html
# Original Perl script by Sirtaj Singh Kang (taj@kde.org)
# Sun Feb 24 14:49:17 CET 2002
# Python translation

import re
import sys
import os
import datetime

# Global variable, equivalent to Perl's %url
url_map = {}
# Global variables for date, equivalent to Perl's $date related logic
# Populated at the start of the script execution
current_day = ""
current_month = ""
current_year = ""

def maplink(tag):
    """
    Resolves a Vim tag to an HTML link or marks it as a bad link.
    Corresponds to Perl's maplink sub.
    """
    if tag in url_map:
        return url_map[tag]
    else:
        # warn "Unknown hyperlink target: $tag\n"; (Perl comment)
        tag = tag.replace('.txt', '')
        tag = tag.replace('<', '&lt;')
        tag = tag.replace('>', '&gt;')
        return f'<code class="badlink">{tag}</code>'

def read_tag_file(tagfile):
    """
    Reads a Vim tags file and populates the global url_map.
    Corresponds to Perl's readTagFile sub.
    """
    global url_map
    try:
        with open(tagfile, 'r', encoding='utf-8', errors='ignore') as tags_f:
            for line in tags_f:
                match = re.match(r'(\S+)\s+(\S+)\s+', line)
                if not match:
                    continue

                tag = match.group(1)
                file_path = match.group(2)
                label = tag

                file_path = file_path.replace('.txt', '.html')
                label = label.replace('.txt', '')

                url_map[tag] = f'<a href="{file_path}#{escurl(tag)}">{esctext(label)}</a>'
    except FileNotFoundError:
        print(f"Error: Can't read tags file '{tagfile}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading tags file '{tagfile}': {e}", file=sys.stderr)
        sys.exit(1)

def esctext(text):
    """
    Escapes special characters in text for HTML display.
    Corresponds to Perl's esctext sub.
    """
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

def escurl(url_str):
    """
    Escapes special characters in a string for use in a URL fragment (anchor name).
    Corresponds to Perl's escurl sub.
    """
    url_str = url_str.replace('"', '%22')
    url_str = url_str.replace('~', '%7E')
    url_str = url_str.replace('<', '%3C')
    url_str = url_str.replace('>', '%3E')
    url_str = url_str.replace('=', '%20') # As per original Perl script
    url_str = url_str.replace('#', '%23')
    url_str = url_str.replace('/', '%2F')
    return url_str

def vim2html(infile):
    """
    Converts a single Vim documentation text file to HTML.
    Corresponds to Perl's vim2html sub.
    """
    global current_day, current_month, current_year
    try:
        with open(infile, 'r', encoding='utf-8', errors='ignore') as in_f:
            base_outfile_name = os.path.basename(infile)
            base_outfile_name = re.sub(r'\.txt$', '', base_outfile_name)
            
            outfile_html = f"{base_outfile_name}.html"

            try:
                with open(outfile_html, 'w', encoding='utf-8') as out_f:
                    head = base_outfile_name.upper()

                    out_f.write(f"""<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<title>VIM: {base_outfile_name}</title>
<link rel="stylesheet" href="vim-stylesheet.css" type="text/css">
</head>
<body>
<h2>{head}</h2>
<pre>
""")
                    inexample = 0 # 0: not in example, 1: marker found, next line is example, 2: in example content
                    
                    for line_num, raw_line in enumerate(in_f):
                        line = raw_line.rstrip('\n') # Equivalent to Perl's chop for newline
                        current_line_for_processing = line

                        # Determine if the current line's output should be wrapped in <code class="example">
                        # This depends on the state *before* processing the current line's markers
                        output_as_example = (inexample == 2)

                        if re.match(r"^\s*[-=]+\s*$", line):
                            out_f.write("</pre><hr><pre>\n")
                            continue
                        
                        # Handle example markers and state transitions
                        if line == ">" or line.endswith(" >"):
                            if line.endswith(" >"):
                                current_line_for_processing = line[:-2]
                            else: # line == ">"
                                current_line_for_processing = ""
                            inexample = 1 # Signal that the *next* line starts example content
                        elif inexample and (line.startswith("<") or (line and not line[0].isspace())):
                            # This line terminates an example block
                            inexample = 0
                            if line.startswith("<"):
                                current_line_for_processing = line[1:]
                            # else current_line_for_processing remains as `line`
                        # If no marker logic hit, inexample (0 or 2) carries over,
                        # and current_line_for_processing is the original `line`.
                        
                        current_line_for_processing = current_line_for_processing.rstrip() # s/\s+$//g;

                        # Tokenize and apply vim highlights
                        # Split by recognized patterns, keeping the delimiters
                        # Pattern: (|...|) or (*...*)
                        tokens = re.split(r'(\|[^\|]+\||\*[^\*]+\*)', current_line_for_processing)
                        
                        out_parts = []
                        for token in tokens:
                            if token is None: # re.split can insert None for non-matching capture groups
                                continue

                            if token.startswith('|') and token.endswith('|') and len(token) > 1:
                                tag_content = token[1:-1]
                                out_parts.append("|" + maplink(tag_content) + "|")
                            elif token.startswith('*') and token.endswith('*') and len(token) > 1:
                                tag_content = token[1:-1]
                                out_parts.append(
                                    f'<b class="vimtag">*{esctext(tag_content)}<a name="{escurl(tag_content)}"></a>*</b>'
                                )
                                # Note: Original Perl script had esctext($1) inside <a> and also for the visible part.
                                # Modern HTML usually puts content inside <a> for named anchors if they are to be visible identifiers,
                                # but `name` attribute itself doesn't display. Vim's *tag* syntax is a visible target.
                                # The Perl code was: <b class="vimtag">\*<a name="escurl($1)">esctext($1)<\/a>\*<\/b>
                                # Let's adjust to closer match the original's visible output if esctext($1) was the link text
                                # The original's `esctext($1)` inside `<a>` is the link text.
                                # For a named anchor, often the content is directly the tag.
                                # The Perl code made `esctext($1)` the content of the `<a>` tag.
                                # Let's try to match the visual structure as much as possible.
                                # The name attribute doesn't need visible content within the <a> for navigation.
                                # However, the Perl output is: *<a name="TAG">TAG</a>*
                                # So, let's replicate that.
                                out_parts[-1] = (
                                    f'<b class="vimtag">*'
                                    f'<a name="{escurl(tag_content)}">{esctext(tag_content)}</a>'
                                    f'*</b>'
                                )

                            else:
                                # Process regular text parts
                                processed_token = esctext(token)
                                processed_token = re.sub(r'CTRL-(\w+)', r'<code class="keystroke">CTRL-\1</code>', processed_token)
                                processed_token = re.sub(r'&lt;(.*?)&gt;', r'<code class="special">&lt;\1&gt;</code>', processed_token) # For <...>
                                processed_token = re.sub(r'\{([^}]*)\}', r'<code class="special">{\1}</code>', processed_token) # For {...}
                                # For [...] with specific keywords
                                processed_token = re.sub(r'\[(range|line|count|offset|cmd|[-+]?num)\]', r'<code class="special">[\1]</code>', processed_token)
                                processed_token = re.sub(r'(Note:?)', r'<code class="note">\1</code>', processed_token, flags=re.IGNORECASE) # gi
                                processed_token = re.sub(r'^(.*)\~$', r'<code class="section">\1</code>', processed_token) # local heading
                                out_parts.append(processed_token)
                        
                        final_line_html = "".join(out_parts)

                        if output_as_example: # True if inexample was 2 at the start of this iteration
                            out_f.write(f'<code class="example">{final_line_html}</code>\n')
                        else:
                            out_f.write(f'{final_line_html}\n')
                        
                        # State transition for the *next* iteration
                        if inexample == 1: # Marker was found on current line
                            inexample = 2  # Next line will be example content
                        # If inexample was 0, it stays 0. If it was 2, it stays 2 (unless an end-of-example marker was found this iteration).

                    out_f.write(f"""</pre>
<p><i>Generated by vim2html on {current_day}.{current_month}.{current_year}</i></p>
</body>
</html>
""")
            except IOError as e:
                print(f"Couldn't write to {outfile_html}: {e}", file=sys.stderr)
                sys.exit(1)

    except FileNotFoundError:
        print(f"Couldn't read from {infile}: File not found.", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Couldn't read from {infile}: {e}", file=sys.stderr)
        sys.exit(1)


def usage():
    """
    Prints usage message and exits.
    Corresponds to Perl's usage sub.
    """
    print("""vim2html.py: converts vim documentation to HTML.
usage:

    vim2html.py <tag file> <text files...>""", file=sys.stderr)
    sys.exit(1)

def write_css():
    """
    Writes the CSS stylesheet file.
    Corresponds to Perl's writeCSS sub.
    """
    css_content = """body { background-color: white; color: black;}
:link { color: rgb(0,137,139); }
:visited { color: rgb(0,100,100);
           background-color: white; /* should be inherit */ }
:active { color: rgb(0,200,200);
          background-color: white; /* should be inherit */ }

B.vimtag { color : rgb(250,0,250); }

h1, h2 { color: rgb(82,80,82); text-align: center; }
h3, h4, h5, h6 { color: rgb(82,80,82); }
.headline { color: rgb(0,137,139); }
.header { color: rgb(164, 32, 246); }
.section { color: rgb(164, 32, 246); }
.keystroke { color: rgb(106, 89, 205); }
.vim { }
.example { color: rgb(0, 0, 255); }
.option { }
.notvi { }
.special { color: rgb(106, 89, 205); }
.note { color: blue; background-color: yellow; }
.sub {}
.badlink { color: rgb(0,37,39); }
"""
    try:
        with open("vim-stylesheet.css", "w", encoding='utf-8') as css_f:
            css_f.write(css_content)
    except IOError as e:
        print(f"Couldn't write stylesheet: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """
    Main execution block.
    """
    global current_day, current_month, current_year

    # Initialize date components
    # Perl:
    # my ($year) = 1900 + (localtime())[5];
    # my ($month) = 1 + (localtime())[4];
    # my ($day) = (localtime())[3];
    now = datetime.datetime.now()
    current_year = str(now.year)
    current_month = str(now.month).zfill(2) #Ensure two digits for month
    current_day = str(now.day).zfill(2)     #Ensure two digits for day


    if len(sys.argv) < 3: # Script name + tag file + at least one text file
        usage()

    tag_file_arg = sys.argv[1]
    text_files_args = sys.argv[2:]

    print("Processing tags...")
    read_tag_file(tag_file_arg)

    for file_arg in text_files_args:
        print(f"Processing {file_arg}...")
        vim2html(file_arg)
    
    print("Writing stylesheet...")
    write_css()
    print("done.")

if __name__ == "__main__":
    main()