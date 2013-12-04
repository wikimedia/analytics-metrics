DOT_FILES=$(wildcard *.dot)

GENERATED_PNG_FILES=$(DOT_FILES:%.dot=%.png)

all: $(GENERATED_PNG_FILES)

clean:
	rm -rf $(GENERATED_PNG_FILES)

%.png: %.dot
	dot -Tpng $< -o $@