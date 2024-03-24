import streamlit as st
import colorsys

def hex_to_rgb(hex_color):
    return [int(hex_color[i:i+2], 16) / 255.0 for i in (1, 3, 5)]  # '#'を除外するためにスライスが(1, 3, 5)

def hex_to_hsl(hex_color):
    rgb_color = hex_to_rgb(hex_color)
    hsl_color = colorsys.rgb_to_hls(*rgb_color)
    return [hsl_color[0], hsl_color[2] * 100, hsl_color[1] * 100]  # 色相、彩度、明度をそれぞれ0-360、0-100、0-100の範囲に変換

def rgb_to_hex(rgb_color):
    return '#' + ''.join([hex(int(color * 255))[2:].zfill(2) for color in rgb_color])

def rotate_hue(hex_color, degrees):
    rgb_color = hex_to_rgb(hex_color)
    hsv_color = colorsys.rgb_to_hsv(*rgb_color)
    
    rotated_hue = (hsv_color[0] + degrees / 360.0) % 1.0
    rotated_color = colorsys.hsv_to_rgb(rotated_hue, hsv_color[1], hsv_color[2])
    
    return rgb_to_hex(rotated_color)

def describe_color_purity(hsl_color):
    h, s, l = hsl_color
    if l == 50 and s == 100:
        st.error("この色は純色です。")
    else:
        pass

st.title('Accent Color Creator')

col1, col2 = st.columns(2)

with col1:
    main_color = st.color_picker('Select your main color', '#ff0000')  # デフォルトのメインカラーを赤色に設定
    st.write('Your main color:', main_color)

    main_rgb_color = hex_to_rgb(main_color)
    st.write(f'R: {main_rgb_color[0]}　G: {main_rgb_color[1]}　B: {main_rgb_color[2]}')

    main_hsl_color = hex_to_hsl(main_color)
    st.write(f'H: {main_hsl_color[0]}　S: {main_hsl_color[1]}%　L: {main_hsl_color[2]}%')
    describe_color_purity(main_hsl_color)

with col2:
    accent_color = rotate_hue(main_color, 120)
    st.color_picker('your accent color', accent_color, disabled=True)   
    st.write('Your accent color:', accent_color)

    accent_rgb_color = hex_to_rgb(accent_color)
    st.write(f'R: {accent_rgb_color[0]}　G: {accent_rgb_color[1]}　B: {accent_rgb_color[2]}')

    accent_hsl_color = hex_to_hsl(accent_color)
    st.write(f'H: {accent_hsl_color[0]}　S: {accent_hsl_color[1]}%　L: {accent_hsl_color[2]}%')
    describe_color_purity(accent_hsl_color)
