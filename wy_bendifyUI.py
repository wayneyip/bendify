# wy_bendifyUI.py
# Author: Wayne Yip
# Date: September 4, 2018

import maya.cmds as cmds
from functools import partial
import wy_bendify
reload (wy_bendify)

def bendifyUI():
    
    # Create window
    if cmds.window('bendifyWin', exists=True):
        cmds.deleteUI('bendifyWin')
    window = cmds.window('bendifyWin', title='Bendify', sizeable=True)
    
    # Create form + UI elements
    form = cmds.formLayout(numberOfDivisions=100)
    startJointText = cmds.textFieldGrp(label='Start Joint', adj=2)
    endJointText = cmds.textFieldGrp(label='End Joint', adj=2)
    globalScaleText = cmds.textFieldGrp(label='Global Scale', adj=2)
    spanIntSlider = cmds.intSliderGrp(label='Number of Spans', 
        field=True, step=2,
        minValue=2, maxValue=20, value=4,
        adj=3
    )
    #startJointBtn = cmds.button(label='Set')
    #endJointBtn = cmds.button(label='Set')

    bendifyBtn = cmds.button(label='Bendify!', 
        command=partial(executeBendify, 
            startJointText, endJointText, 
            globalScaleText, spanIntSlider
        )
    )
    applyBtn = cmds.button(label='Apply', 
        command=partial(applyBendify,
            startJointText, endJointText, 
            globalScaleText, spanIntSlider
        )
    )
    closeBtn = cmds.button(label='Close', 
        command="cmds.deleteUI('bendifyWin')"
    )

    # Format UI elements
    cmds.formLayout(form, edit=True,
        attachForm=[
            (startJointText, 'top', 5),
            (startJointText, 'left', 0),
            (startJointText, 'right', 0),
            #(startJointBtn, 'top', 5),
            #(startJointBtn, 'right', 10),

            (endJointText, 'left', 0),
            (endJointText, 'right', 0),
            #(endJointBtn, 'right', 10),

            (globalScaleText, 'left', 0),
            (globalScaleText, 'right', 0),

            (spanIntSlider, 'left', 0),
            (spanIntSlider, 'right', 0),
            (spanIntSlider, 'bottom', 5),

            (bendifyBtn, 'left', 5),
            (bendifyBtn, 'bottom', 5),
            (applyBtn, 'bottom', 5),
            (closeBtn, 'bottom', 5),
            (closeBtn, 'right', 5)
        ],
            attachControl=[
            #(startJointText, 'right', 0, startJointBtn),
            (startJointText, 'bottom', 5, endJointText),

            #(endJointText, 'right', 0, endJointBtn),
            #(startJointBtn, 'bottom', 5, endJointBtn),
            (endJointText, 'bottom', 5, globalScaleText),

            (globalScaleText, 'bottom', 5, spanIntSlider),
            (spanIntSlider, 'bottom', 5, bendifyBtn),
            
            (bendifyBtn, 'right', 5, applyBtn),
            (closeBtn, 'left', 5, applyBtn)
        ],
        attachPosition=[
            #(endJointBtn, 'top', 0, 23),
            (bendifyBtn, 'right', 0, 33),
            (applyBtn, 'left', 0, 34),
            (applyBtn, 'right', 0, 66),
        ]
    )

    cmds.showWindow(window)


def executeBendify(startJointText, endJointText, globalScaleText, spanIntSlider, *args):

    applyBendify(startJointText, endJointText, globalScaleText, spanIntSlider)
    cmds.deleteUI('bendifyWin')


def applyBendify(startJointText, endJointText, globalScaleText, spanIntSlider, *args):

    startJoint = cmds.textFieldGrp(startJointText, q=True, text=True)
    endJoint = cmds.textFieldGrp(endJointText, q=True, text=True)
    globalScale = cmds.textFieldGrp(globalScaleText, q=True, text=True)
    spanCount = cmds.intSliderGrp(spanIntSlider, q=True, value=True)

    wy_bendify.bendify(startJoint, endJoint, globalScale, spanCount)
