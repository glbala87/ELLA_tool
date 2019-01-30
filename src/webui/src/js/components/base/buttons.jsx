/*

$blue: hsl(205,45,35);
$green: hsl(175,45,35);
$purple: hsl(235,45,35);
$black: hsl(0,0,0);
$white: hsl(0,0,100);
$yellow: hsla(35, 95, 40, 1);
$yellow-50: hsla(35, 95, 40, 0.5);

$red: hsla(10,45,35,1);

$blue-75-on-white: rgb(100, 136, 160);
$blue-50-on-white: rgb(156, 174, 191);
$blue-25-on-white: rgb(203, 215, 223);

*/

import React from 'react'
import styled from 'styled-components'

function color(p) {
    if (p.blue) {
        return 'blue'
    }
    return 'red'
}

export const Button = styled.button`
    height: 2.6rem;
    font-family: 'Work Sans', sans-serif;
    font-size: 1.2rem;
    font-weight: 500;
    letter-spacing: 0.1rem;
    word-spacing: 0.2rem;
    text-transform: uppercase;
    padding: 0.25rem 0.75rem;
    padding-top: 0.4rem;
    white-space: nowrap;
    border-radius: 0;
    height: 2.6rem;
    box-shadow: 0 0.3rem 0 rgba(0, 0, 0, 0.05);
    transition: all 0.3s;
    outline: none;
    border: 1px solid Transparent;
    color: white;
    background-color: ${(p) => color(p)};
`

export const TestButton = () => <Button redasd>Test</Button>
