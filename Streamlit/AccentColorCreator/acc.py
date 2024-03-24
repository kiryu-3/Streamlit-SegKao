import streamlit as st
import colorsys

def hex_to_rgb(hex_color):
    return [int(hex_color[i:i+2], 16) / 255.0 for i in (1, 3, 5)]  # '#'を除外するためにスライスが(1, 3, 5)

def rgb_to_hex(rgb_color):
    return '#' + ''.join([hex(int(color * 255))[2:].zfill(2) for color in rgb_color])

def rotate_hue(hex_color, degrees):
    rgb_color = hex_to_rgb(hex_color)
    hsv_color = colorsys.rgb_to_hsv(*rgb_color)
    
    rotated_hue = (hsv_color[0] + degrees / 360.0) % 1.0
    rotated_color = colorsys.hsv_to_rgb(rotated_hue, hsv_color[1], hsv_color[2])
    
    return rgb_to_hex(rotated_color)

st.title('Accent Color Creator')

col1, col2 = st.columns(2)

with col1:
    main_color = st.color_picker('Select your main color', '#ff0000')  # デフォルトのメインカラーを赤色に設定
    st.write('Your main color:', main_color)

    main_rgb_color = hex_to_rgb(main_color)
    st.write(f'R: {main_rgb_color[0]}　G: {main_rgb_color[1]}　B: {main_rgb_color[2]}')

with col2:
    accent_color = rotate_hue(main_color, 120)
    st.color_picker('your accent color', accent_color, disabled=True)   
    st.write('Your accent color:', accent_color)

    accent_rgb_color = hex_to_rgb(accent_color)
    st.write(f'R: {accent_rgb_color[0]}　G: {accent_rgb_color[1]}　B: {accent_rgb_color[2]}')
