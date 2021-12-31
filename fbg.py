"""Font bitmap generator"""
from sys import argv
from subprocess import call
from PIL import Image, ImageFont, ImageDraw

if __name__ == '__main__':
    with open('font.zig', 'w') as file:
        file.write(f'pub const data: [128] = .{{')
    
        # Generate padding entries to match ASCII numbering
        for i in range(32):
            file.write(f'\n    .{{')
            for x in range(5):
                file.write(f'\n        .{{')
                for y in range(5):
                        file.write(f'false,')
                file.write(f'}},')
            file.write(f'\n        }},')

        # Generate letter entries
        font = ImageFont.truetype(font=argv[1])
        for i in range(32, 128):
            letter = chr(i)
            image = Image.new(mode='1', size=(5, 5), color='white')
            draw = ImageDraw.Draw(im=image)
            draw.text(xy=(0, 0), text=letter, font=font, anchor='lt', color='black')
            
            file.write(f'\n    .{{')
            for x in range(5):
                file.write(f'\n        .{{')
                for y in range(5):
                    if image.getpixel((x, y)):
                        file.write(f'false,')
                    else:
                        file.write(f'true,')
                file.write(f'}},')
            file.write(f'\n        }},')

        file.write(f'\n}};')