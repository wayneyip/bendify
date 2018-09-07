# wy_bendify.py
# Author: Wayne Yip
# Date: August 29, 2018

import maya.cmds as cmds

def bendify(startJoint, endJoint, globalScale, spanNum):

    # Validate start joint
    if (not cmds.objExists(startJoint)
        or cmds.nodeType(startJoint) != 'joint' 
    ):
        cmds.confirmDialog( title='Bendify Error', message='Invalid start joint')
        return
    
    # Validate end joint
    if (not cmds.objExists(endJoint)
        or cmds.nodeType(endJoint) != 'joint'
    ):
        cmds.confirmDialog( title='Bendify Error', message='Invalid end joint')
        return

    # Validate global scale
    if ( not cmds.objExists(globalScale) 
        or not '.' in globalScale
    ):
        cmds.confirmDialog( title='Bendify Error', message='Invalid global scale')
        return
    
    masterCtrl = getObjFromAttr(globalScale)
    
    mainCurve = createCurve(startJoint, endJoint, spanNum)

    curves = splitCurve(mainCurve, spanNum)

    clusters = clusterCurves(curves)

    clusterGrps = groupClusters(clusters)
    
    bones = createBones(clusters)
    
    ikHandles = createIkHandles(bones)
    
    parentIkHandles(ikHandles, clusterGrps)
    
    ctrls = createCtrls(bones, startJoint, endJoint)
    
    ctrlGrps = groupCtrls(ctrls, bones)

    constrGrps = createConstrGrps(ctrls, startJoint)
    
    constrainIKsToCtrls(constrGrps, clusterGrps, ctrls, bones, spanNum)
    
    constrainCtrlGrpsToJoints(ctrlGrps, startJoint, endJoint)
    
    makeBonesBendy(curves, bones, globalScale)
    
    groupAll(
        masterCtrl, ctrlGrps,
        curves, clusterGrps,
        bones, constrGrps, startJoint
    )

def createCurve(startJoint, endJoint, spanNum):

    startPos = cmds.joint(startJoint, q=True, position=True)
    endPos = cmds.joint(endJoint, q=True, position=True)

    # Create CV curve across start and end joint 
    curve = cmds.curve(
        degree=1, 
        point=[startPos, endPos], 
        knot=[0,1]
    )

    # Rebuild curve with given number of spans
    curve = cmds.rebuildCurve(
        curve, 
        degree=1, 
        spans=spanNum
    )
    curveName = removeSuffix(startJoint) + '_bendy_CRV'
    cmds.rename(curve, curveName)

    return curveName


def splitCurve(curve, spanNum):
    
    # Get a list of fractions for each split point
    # ( e.g. spanNum = 4: [0.25, 0.50, 0.75] )
    parameters = []
    for i in range(1, spanNum):
        parameters.append( float(i) / spanNum)

    # Split curve at defined points
    splitCurves = cmds.detachCurve(
        curve, 
        parameter=parameters
    )

    # Rename split curves
    renamedSplitCurves = []
    for i, splitCurve in enumerate(splitCurves):

        curveName = removeSuffix(splitCurve) + '_%s_CRV' % (i+1)
        curveName = cmds.rename(splitCurve, curveName)
        renamedSplitCurves.append(curveName)

    cmds.delete(curve)
    return renamedSplitCurves


def clusterCurves(curves):

    clusters = []

    # First cluster
    firstCurve = curves[0]
    firstCluster = cmds.cluster(
        firstCurve + '.cv[0]', 
        name=removeSuffix(firstCurve) + '_CL'
    )
    clusters.append(firstCluster[1])

    # Middle clusters
    for i in range(len(curves) - 1):
        midCluster = cmds.cluster(
            curves[i] + '.cv[1]', 
            curves[i + 1] + '.cv[0]',
            name=removeSuffix(curves[i + 1]) + '_CL'
        )
        clusters.append(midCluster[1])

    # Last cluster
    lastCurve = curves[len(curves) - 1]
    lastCluster = cmds.cluster(
        lastCurve + '.cv[1]',
        name=removeSuffix(removeSuffix(lastCurve)) + '_%s_CL' % (len(curves)+1)
    )
    clusters.append(lastCluster[1])

    return clusters


def groupClusters(clusters):

    clusterGrps = []

    for cluster in clusters:

        # Group cluster
        grpName = removeSuffix(cluster) + '_CL_GRP'
        cmds.group(cluster, name=grpName)

        # Get cluster position
        clusterPos = cmds.xform(
            cluster, q=True,
            rotatePivot=True,
            worldSpace=True
        )

        # Align group node's position to cluster
        cmds.move(
            clusterPos[0], clusterPos[1], clusterPos[2],
            grpName + ".scalePivot", 
            grpName + ".rotatePivot",
            absolute=True 
        )

        clusterGrps.append(grpName)

    return clusterGrps


def createBones(clusters):

    bones = []

    cmds.select(clear=True)

    for i, cluster in enumerate(clusters):
       
        # Get cluster position
        clusterPos = cmds.xform(
            cluster, 
            q=True, 
            rotatePivot=True, 
            worldSpace=True
        )
        # Create bone at cluster position
        boneName = removeSuffix(cluster) + '_JNT'
        cmds.joint(position=clusterPos, name=boneName)
        
        # Orient previous bone to newly created bone
        if i >= 1:
            previousBone = bones[len(bones) - 1]
            cmds.joint(
                previousBone, edit=True,
                orientJoint='xyz',
                secondaryAxisOrient='yup'
            )
        # Orient last bone to previous bone
        if i == len(clusters) - 1:
            previousBone = bones[len(bones) - 1]
            orient = cmds.joint(
                previousBone, q=True,
                orientation=True
            )
            cmds.joint(
                boneName, edit=True,
                orientation=orient
            )
        bones.append(boneName)

    return bones 


def createIkHandles(bones):
    
    ikHandles = []

    for i in range(len(bones) - 1):
        
        ikName = removeSuffix(bones[i]) + '_IK'
        cmds.ikHandle(
            startJoint=bones[i],
            endEffector=bones[i + 1],
            name=ikName
        )
        ikHandles.append(ikName)

    return ikHandles


def parentIkHandles(ikHandles, clusterGrps):

    for i in range(len(ikHandles)):
        cmds.parent(
            ikHandles[i], 
            clusterGrps[i + 1]
        )


def createCtrls(bones, startJoint, endJoint):
    
    def createCtrl(bone, pos, joint=None):

        # If joint already has a control (e.g. when bendifying a joint chain),
        # get that control and return it
        if joint is not None:
            constraints = cmds.listConnections(joint, type='pointConstraint')
            if constraints is not None and len(constraints) > 0:
                constraint = constraints[0]
                ctrlGrp = removeSuffix(constraint)
                ctrl = removeSuffix(ctrlGrp)

                ctrlName = removeSuffix(removeSuffix(bone)) + '_%s_CTRL' % pos 
                ctrl = cmds.rename(ctrl, ctrlName)
                return ctrl

        ctrl = removeSuffix(removeSuffix(bone)) + '_%s_CTRL' % pos
        cmds.circle(normal=(1,0,0), name=ctrl, constructionHistory=False)
        return ctrl
    
    ctrls = []

    startCtrl = createCtrl(bones[0], 'start', startJoint)
    midCtrl = createCtrl(bones[len(bones) / 2], 'mid')
    endCtrl = createCtrl(bones[len(bones) - 1], 'end', endJoint)

    ctrls.append(startCtrl)
    ctrls.append(midCtrl)
    ctrls.append(endCtrl)

    return ctrls


def groupCtrls(ctrls, bones):

    def groupCtrl(ctrl, bone):
        ctrlGrp = ctrl + '_GRP'
        if cmds.objExists(ctrlGrp):
            return ctrlGrp

        cmds.group(ctrl, name=ctrlGrp)

        # Parent group node to bone, then unparent --
        # auto-orients the control to the bone.
        #
        cmds.parent(ctrlGrp, bone, relative=True)
        cmds.parent(ctrlGrp, world=True)

        return ctrlGrp

    ctrlGrps = []

    startCtrlGrp = groupCtrl(ctrls[0], bones[0])
    midCtrlGrp = groupCtrl(ctrls[1], bones[len(bones) / 2])
    endCtrlGrp = groupCtrl(ctrls[2], bones[len(bones) - 1])
    
    ctrlGrps.append(startCtrlGrp)
    ctrlGrps.append(midCtrlGrp)
    ctrlGrps.append(endCtrlGrp)

    return ctrlGrps


def createConstrGrps(ctrls, startJoint):

    def createConstrGrp(ctrl, pos):

        def moveToCtrl(obj, ctrlPos):
            cmds.move(
                ctrlPos[0], ctrlPos[1], ctrlPos[2],
                obj + ".scalePivot", 
                obj + ".rotatePivot",
                absolute=True 
            )

        # Get control's position
        ctrlPos = cmds.xform(
            ctrl, q=True,
            translation=True, worldSpace=True
        )

        # Empty group node for IK handles to be parent constrained to
        parent = cmds.group(empty=True, n=ctrl + '_PARENT')
        moveToCtrl(parent, ctrlPos)

        if (pos == 'start' or pos == 'end'):
            cmds.connectAttr(ctrl + '.rotate', parent + '.rotate')

        # Group node for orient constraint
        orient = cmds.group(parent, n=ctrl + '_ORIENT')
        moveToCtrl(orient, ctrlPos)

        # For start and end controls, the start joint drives the orientation
        if (pos == 'start' or pos == 'end'):
            orientConstr = cmds.orientConstraint(startJoint, orient, mo=True)[0]
            moveToCtrl(orientConstr, ctrlPos)

        # For the middle (bendy) control, the control drives the orientation
        else:
            orientConstr = cmds.orientConstraint(ctrl, orient, mo=True)[0]
            moveToCtrl(orientConstr, ctrlPos)

        # Group node for point constraint
        point = cmds.group(orient, n=ctrl + '_POINT')
        moveToCtrl(point, ctrlPos)

        pointConstr = cmds.pointConstraint(ctrl, point, mo=True)[0]
        moveToCtrl(pointConstr, ctrlPos)
        
        return parent

    parentNodes = []

    startCtrl = ctrls[0]
    midCtrl = ctrls[1]
    endCtrl = ctrls[2]

    startParent = createConstrGrp(startCtrl, 'start')
    midParent = createConstrGrp(midCtrl, 'mid')
    endParent = createConstrGrp(endCtrl, 'end')

    parentNodes.append(startParent)
    parentNodes.append(midParent)
    parentNodes.append(endParent)

    return parentNodes


def constrainIKsToCtrls(constrGrps, clusterGrps, ctrls, bones, spans):

    startParent = constrGrps[0]
    midParent = constrGrps[1]
    endParent = constrGrps[2]

    startCtrl = ctrls[0]
    midCtrl = ctrls[1]
    endCtrl = ctrls[2]

    half = len(clusterGrps) / 2
    end = len(clusterGrps) - 1

    # Constraint first bendy bone to start control 
    cmds.parentConstraint(startCtrl, bones[0], maintainOffset=True)

    # Constrain IKs/clusters to controls
    for i, clusterGrp in enumerate(clusterGrps):
        
        # Quadratic function --
        # distributes IK constraint weights such that
        # they increase towards the mid control.
        #
        midWeight = -(4.0/spans/spans)*i*i + (4.0/spans)*i
        sideWeight = 1.0 - midWeight

        # First IK/cluster
        if i == 0:
            cmds.parentConstraint(startCtrl, clusterGrps[i], mo=True, weight=sideWeight)
        
        # First half of IKs/clusters
        elif 0 < i and i < half: 
            cmds.parentConstraint(startParent, clusterGrps[i], mo=True, weight=sideWeight)
            cmds.parentConstraint(midParent, clusterGrps[i], mo=True, weight=midWeight)
        
        # Middle IK/cluster
        elif i == half: 
            cmds.parentConstraint(midParent, clusterGrps[i], mo=True, weight=midWeight)

        # Last half of IKs/clusters
        elif half < i and i < end:
            cmds.parentConstraint(midParent, clusterGrps[i], mo=True, weight=midWeight)
            cmds.parentConstraint(endParent, clusterGrps[i], mo=True, weight=sideWeight)

        # Last IK/cluster
        elif i == end:
            cmds.parentConstraint(endCtrl, clusterGrps[i], mo=True, weight=sideWeight)


def constrainCtrlGrpsToJoints(ctrlGrps, startJoint, endJoint):
    
    startCtrlGrp = ctrlGrps[0]
    midCtrlGrp = ctrlGrps[1]
    endCtrlGrp = ctrlGrps[2]

    # Constrain start and end control groups to main joints
    cmds.pointConstraint(startJoint, startCtrlGrp, maintainOffset=True)
    cmds.pointConstraint(endJoint, endCtrlGrp, maintainOffset=True)
    
    # Constrain mid control group to start and end 
    cmds.parentConstraint(startCtrlGrp, midCtrlGrp, maintainOffset=True)
    cmds.parentConstraint(endCtrlGrp, midCtrlGrp, maintainOffset=True)


def makeBonesBendy(curves, bones, globalScale):

    for i, curve in enumerate(curves):

        # Create curveInfo node
        # to get arclength of each curve  
        curveInfo = cmds.arclen(curve, constructionHistory=True)
        curveInfo = cmds.rename(curveInfo, curve + 'Info')

        # Create multiplyDivide node
        arclenDiv = removeSuffix(curveInfo) + '_arclen_MD'
        arclenDiv = cmds.createNode('multiplyDivide', name=arclenDiv)
        cmds.setAttr(arclenDiv + '.operation', 2) # divide

        # Divide curve's current arclength by base arclength,
        # to get a multiplier for bone length
        cmds.connectAttr(curveInfo + '.arcLength', arclenDiv + '.input1X')
        baseArclen = cmds.getAttr(arclenDiv + '.input1X')
        cmds.setAttr(arclenDiv + '.input2X', baseArclen)

        # Create multiplyDivide node 
        # to get global scale multiplier
        scaleDiv = removeSuffix(curveInfo) + '_scale_MD'
        scaleDiv = cmds.createNode('multiplyDivide', name=scaleDiv)
        cmds.setAttr(scaleDiv + '.operation', 2) # divide

        # Divide bone length multiplier by global scale
        cmds.connectAttr(arclenDiv + '.outputX', scaleDiv + '.input1X')
        cmds.connectAttr(           globalScale, scaleDiv + '.input2X')

        # Scale bone length by this multiplier
        cmds.connectAttr(scaleDiv + '.outputX', bones[i] + '.scaleX')


def groupAll(
        masterCtrl, ctrlGrps,
        curves, clusterGrps,
        bones, constrGrps, startJoint
    ):
    
    def group(nameSuffix, objList):
    
        grpName = basename + nameSuffix
        grp = cmds.group(empty=True, n=grpName)
        for obj in objList:
            cmds.parent(obj, grp)

        return grp
    
    # Get base name
    # (e.g. L_elbow_bendy_1_CRV -> L_elbow_bendy)
    basename = removeSuffix(removeSuffix(curves[0]))

    # Group controls, curves, clusters into separate groups 
    ctrlGrpsGrp = group('_ctrls_GRP', ctrlGrps)
    curvesGrp = group('_curves_GRP', curves)
    clusterGrpsGrp = group('_clusterGrps_GRP', clusterGrps)

    # Group bone chain into a separate group
    bonesGrp = basename + '_Bones_GRP'
    bonesGrp = cmds.group(bones[0], n=bonesGrp)

    # Group the constraint group nodes
    pointConstrGrps = []
    for parentConstrGrp in constrGrps:
        orientConstrGrp = cmds.listRelatives(parentConstrGrp, parent=True)[0]
        pointConstrGrp = cmds.listRelatives(orientConstrGrp, parent=True)[0]
        pointConstrGrps.append(pointConstrGrp)
    constrGrpsGrp = group('_constrGrps_GRP', pointConstrGrps)

    # Parent every group to a master group
    masterGrp = basename + '_GRP'
    masterGrp = cmds.group(empty=True, n=masterGrp)
    cmds.parent(curvesGrp, masterGrp)
    cmds.parent(clusterGrpsGrp, masterGrp)
    cmds.parent(bonesGrp, masterGrp)
    cmds.parent(constrGrpsGrp, masterGrp)

    # Parent controls under master control 
    cmds.parent(ctrlGrpsGrp, masterCtrl)

    # Final constraining
    cmds.parentConstraint(startJoint, ctrlGrpsGrp, maintainOffset=True)
    cmds.parentConstraint(startJoint, clusterGrpsGrp, maintainOffset=True)

    cmds.scaleConstraint(masterCtrl, bonesGrp, maintainOffset=True)
    cmds.scaleConstraint(masterCtrl, constrGrpsGrp, maintainOffset=True)

    # Lock scale Y/Z for each control
    for ctrlGrp in ctrlGrps:
        ctrl = cmds.listRelatives(ctrlGrp, children=True)[0]
        cmds.setAttr(ctrl + '.scaleY', lock=True)
        cmds.setAttr(ctrl + '.scaleZ', lock=True)


def getObjFromAttr(attr):
    splitName = attr.split('.')
    splitName.pop()
    return ''.join(splitName)


def removeSuffix(name):
    splitName = name.split('_')
    splitName.pop()
    return '_'.join(splitName)
