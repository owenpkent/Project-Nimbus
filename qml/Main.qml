import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Controls.Basic 2.15 as Basic
import QtQuick.Layouts 1.15
import "components" as Comp
import "layouts" as Layouts

ApplicationWindow {
    id: root
    visible: true
    width: 1024
    height: 600
    minimumWidth: 700
    minimumHeight: 450
    title: "Project Nimbus - QML UI"
    background: Rectangle { color: "black" }

    // Scale factor bound to Python bridge; default 1.0
    property real scaleFactor: controller ? controller.scaleFactor : 1.0
    
    // Current profile and layout type
    property string currentProfile: controller ? controller.getCurrentProfile() : "flight_simulator"
    property string layoutType: controller ? controller.getLayoutType() : "flight_sim"
    
    // Guard: prevents Edit Layout menu from appearing during init
    property bool _appReady: false

    // Timer to delay _appReady until menu bar is fully stable
    Timer {
        id: appReadyTimer
        interval: 500
        repeat: false
        onTriggered: root._appReady = true
    }

    // Track available profiles for dynamic updates
    property var availableProfiles: controller ? controller.getAvailableProfiles() : []
    
    // Initialize window reference for game focus mode
    Component.onCompleted: {
        if (controller) {
            controller.setWindow(root)
        }
        appReadyTimer.start()
    }
    
    // Global mouse tracker for game focus mode
    // This detects when user starts/stops interacting with the window
    MouseArea {
        id: globalMouseTracker
        anchors.fill: parent
        z: -1  // Behind everything so it doesn't block other mouse areas
        propagateComposedEvents: true
        acceptedButtons: Qt.AllButtons
        
        onPressed: function(mouse) {
            if (controller) controller.onMousePressed()
            mouse.accepted = false  // Let event propagate to children
        }
        
        onReleased: function(mouse) {
            if (controller) controller.onMouseReleased()
            mouse.accepted = false
        }
    }
    
    // Update when profile changes
    Connections {
        target: controller
        function onProfileChanged(profileId) {
            root.currentProfile = profileId
        }
        function onLayoutTypeChanged(newLayoutType) {
            root.layoutType = newLayoutType
        }
        function onProfilesListChanged() {
            // Refresh profile list when profiles are added/deleted
            root.availableProfiles = controller.getAvailableProfiles()
        }
        function onProfileSaved(success) {
            if (success) {
                saveNotification.show("Profile saved successfully")
            } else {
                saveNotification.show("Failed to save profile")
            }
        }
        function onNoFocusModeChanged(enabled) {
            // Update menu checkbox when mode changes
            noFocusModeItem.checked = enabled
        }
    }
    
    // Simple notification popup
    Rectangle {
        id: saveNotification
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 50
        width: notificationLabel.width + 40
        height: 40
        radius: 8
        color: "#333"
        border.color: "#555"
        border.width: 1
        opacity: 0
        z: 1000
        
        function show(message) {
            notificationLabel.text = message
            notificationAnimation.start()
        }
        
        Label {
            id: notificationLabel
            anchors.centerIn: parent
            color: "white"
            font.pixelSize: 14
        }
        
        SequentialAnimation {
            id: notificationAnimation
            NumberAnimation { target: saveNotification; property: "opacity"; to: 1; duration: 200 }
            PauseAnimation { duration: 2000 }
            NumberAnimation { target: saveNotification; property: "opacity"; to: 0; duration: 500 }
        }
    }

    // Save Profile As Dialog
    Dialog {
        id: saveAsDialog
        title: "Save Profile As"
        modal: true
        anchors.centerIn: parent
        width: 400
        height: 280
        
        background: Rectangle {
            color: "#2a2a2a"
            border.color: "#555"
            border.width: 1
            radius: 8
        }
        
        header: Label {
            text: saveAsDialog.title
            color: "white"
            font.pixelSize: 16
            font.bold: true
            padding: 16
            background: Rectangle { color: "#333"; radius: 8 }
        }
        
        contentItem: Column {
            spacing: 16
            padding: 16
            
            Column {
                spacing: 6
                width: parent.width - 32
                
                Label {
                    text: "Profile Name:"
                    color: "#ccc"
                    font.pixelSize: 13
                }
                Basic.TextField {
                    id: profileNameField
                    width: parent.width
                    placeholderText: "Enter profile name..."
                    color: "white"
                    font.pixelSize: 14
                    background: Rectangle {
                        color: "#1a1a1a"
                        border.color: profileNameField.activeFocus ? "#4a9eff" : "#555"
                        border.width: 1
                        radius: 4
                    }
                }
            }
            
            Column {
                spacing: 6
                width: parent.width - 32
                
                Label {
                    text: "Description (optional):"
                    color: "#ccc"
                    font.pixelSize: 13
                }
                Basic.TextField {
                    id: profileDescField
                    width: parent.width
                    placeholderText: "Enter description..."
                    color: "white"
                    font.pixelSize: 14
                    background: Rectangle {
                        color: "#1a1a1a"
                        border.color: profileDescField.activeFocus ? "#4a9eff" : "#555"
                        border.width: 1
                        radius: 4
                    }
                }
            }
        }
        
        footer: Row {
            spacing: 12
            padding: 16
            layoutDirection: Qt.RightToLeft
            
            Basic.Button {
                text: "Save"
                enabled: profileNameField.text.trim().length > 0
                onClicked: {
                    var newId = controller.createProfileAs(
                        profileNameField.text.trim(),
                        profileDescField.text.trim()
                    )
                    if (newId !== "") {
                        saveNotification.show("Profile '" + profileNameField.text.trim() + "' created")
                        controller.switchProfile(newId)
                    } else {
                        saveNotification.show("Failed to create profile")
                    }
                    profileNameField.text = ""
                    profileDescField.text = ""
                    saveAsDialog.close()
                }
                contentItem: Label {
                    text: parent.text
                    color: parent.enabled ? "white" : "#888"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 80
                    implicitHeight: 32
                    color: parent.enabled ? (parent.down ? "#2563eb" : "#3b82f6") : "#444"
                    radius: 4
                }
            }
            
            Basic.Button {
                text: "Cancel"
                onClicked: {
                    profileNameField.text = ""
                    profileDescField.text = ""
                    saveAsDialog.close()
                }
                contentItem: Label {
                    text: parent.text
                    color: "#ccc"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 80
                    implicitHeight: 32
                    color: parent.down ? "#444" : "#333"
                    border.color: "#555"
                    border.width: 1
                    radius: 4
                }
            }
        }
        
        onOpened: {
            profileNameField.text = ""
            profileDescField.text = ""
            profileNameField.forceActiveFocus()
        }
    }

    // Menus (safe dark mode for top bar only)
    menuBar: MenuBar {
        background: Rectangle { color: "#2a2a2a" }
        delegate: MenuBarItem {
            id: control
            implicitHeight: 30
            contentItem: Label {
                text: control.text
                color: "white"
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                leftPadding: 10
                rightPadding: 10
            }
            background: Rectangle {
                color: control.hovered ? "#3a3a3a" : "#2a2a2a"
            }
        }

        Menu {
            id: fileMenu
            title: qsTr("File")
            
            // Profile submenu
            Menu {
                id: profileMenu
                title: qsTr("Profile")
                
                Instantiator {
                    id: profileInstantiator
                    model: root.availableProfiles
                    delegate: MenuItem {
                        text: modelData.name
                        checkable: true
                        checked: root.currentProfile === modelData.id
                        onTriggered: {
                            fileMenu.close()
                            Qt.callLater(function() {
                                if (controller) controller.switchProfile(modelData.id)
                            })
                        }
                    }
                    onObjectAdded: function(index, object) { profileMenu.insertItem(index, object) }
                    onObjectRemoved: function(index, object) { profileMenu.removeItem(object) }
                }
            }
            
            MenuItem {
                text: qsTr("Save Profile")
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        if (controller) controller.saveCurrentProfile()
                    })
                }
            }
            MenuItem {
                text: qsTr("Save Profile As...")
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        saveAsDialog.open()
                    })
                }
            }
            MenuItem {
                text: qsTr("Reset Profile to Defaults")
                enabled: controller ? controller.isBuiltinProfile(root.currentProfile) : false
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        if (controller) {
                            controller.resetProfile(root.currentProfile)
                            saveNotification.show("Profile reset to defaults")
                        }
                    })
                }
            }
            
            MenuSeparator {}
            
            MenuItem {
                text: qsTr("Open Profiles Folder...")
                onTriggered: {
                    fileMenu.close()
                    Qt.callLater(function() {
                        if (controller) controller.openProfilesFolder()
                    })
                }
            }
            
            MenuSeparator {}
            MenuItem { text: qsTr("Exit"); onTriggered: Qt.quit() }
        }
        
        // Edit Layout — top-level menu, visible only for custom layout
        // Deferred via Loader to prevent menu appearing during startup
        Loader {
            active: root._appReady && root.layoutType === "custom"
            sourceComponent: Menu {
                id: editLayoutMenu
                title: qsTr("Edit Layout")
                Component.onCompleted: {
                    // Insert into menu bar after Settings
                    menuBar.insertMenu(3, editLayoutMenu)
                }
                Component.onDestruction: {
                    menuBar.removeMenu(editLayoutMenu)
                }
                MenuItem {
                    text: layoutLoader.item && layoutLoader.item.editMode ? qsTr("✓ Done Editing Layout") : qsTr("Edit Layout...")
                    onTriggered: {
                        editLayoutMenu.close()
                        Qt.callLater(function(){
                            if (layoutLoader.item) {
                                layoutLoader.item.editMode = !layoutLoader.item.editMode
                                if (!layoutLoader.item.editMode) layoutLoader.item._saveLayout()
                            }
                        })
                    }
                }
            }
        }

        // Settings menu
        Menu {
            id: settingsMenu
            title: qsTr("Settings")
            
            MenuItem { 
                text: qsTr("Axis Configuration...")
                visible: root.layoutType !== "custom"
                height: visible ? implicitHeight : 0
                onTriggered: { 
                    settingsMenu.close()
                    Qt.callLater(function(){ if (controller) controller.openAxisSettings(); })
                } 
            }
            MenuItem { 
                text: qsTr("Button Modes...")
                visible: root.layoutType !== "custom"
                height: visible ? implicitHeight : 0
                onTriggered: { 
                    settingsMenu.close()
                    Qt.callLater(function(){ if (controller) controller.openButtonSettings(); })
                } 
            }
        }
        
        Menu {
            id: viewMenu
            title: qsTr("View")
            MenuItem {
                id: noFocusModeItem
                text: qsTr("Game Focus Mode")
                checkable: true
                checked: controller ? controller.noFocusMode : false
                enabled: controller ? controller.isNoFocusModeAvailable() : false
                onTriggered: { 
                    viewMenu.close()
                    Qt.callLater(function(){ 
                        if (controller) controller.noFocusMode = checked
                    })
                }
            }
            MenuSeparator {}
            MenuItem {
                id: debugBordersItem
                text: qsTr("Debug Borders")
                checkable: true
                checked: controller ? controller.debugBorders : false
                onTriggered: { viewMenu.close(); Qt.callLater(function(){ if (controller) controller.debugBorders = checked; }); }
            }
        }
        
        Menu {
            id: helpMenu
            title: qsTr("Help")
            MenuItem {
                text: qsTr("Getting Started...")
                onTriggered: {
                    helpMenu.close()
                    Qt.callLater(function(){ gettingStartedDialog.open(); })
                }
            }
            MenuItem {
                text: qsTr("Feature Guide...")
                onTriggered: {
                    helpMenu.close()
                    Qt.callLater(function(){ featureGuideDialog.open(); })
                }
            }
            MenuSeparator {}
            MenuItem { 
                text: qsTr("GitHub Repository")
                onTriggered: { 
                    helpMenu.close()
                    Qt.openUrlExternally("https://github.com/owenpkent/Project-Nimbus")
                } 
            }
            MenuSeparator {}
            MenuItem { 
                text: qsTr("About Project Nimbus...")
                onTriggered: { 
                    helpMenu.close()
                    Qt.callLater(function(){ aboutDialog.open(); })
                } 
            }
        }
    }
    
    // About Dialog
    Dialog {
        id: aboutDialog
        title: "About Project Nimbus"
        modal: true
        anchors.centerIn: parent
        width: 450
        height: 320
        
        background: Rectangle {
            color: "#2a2a2a"
            border.color: "#555"
            border.width: 1
            radius: 8
        }
        
        header: Label {
            text: aboutDialog.title
            color: "white"
            font.pixelSize: 16
            font.bold: true
            padding: 16
            background: Rectangle { color: "#333"; radius: 8 }
        }
        
        contentItem: Column {
            spacing: 16
            padding: 20
            
            Image {
                source: "qrc:/logo.png"
                width: 80
                height: 80
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                visible: status === Image.Ready
            }
            
            Label {
                text: "Project Nimbus"
                color: "white"
                font.pixelSize: 20
                font.bold: true
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "Version " + (controller ? controller.getVersion() : "1.4.0")
                color: "#aaa"
                font.pixelSize: 14
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "Virtual controller interface for accessibility and adaptive gaming.\nTransforms mouse input into virtual joystick commands."
                color: "#ccc"
                font.pixelSize: 12
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                width: parent.width - 40
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "© 2024-2025 Owen Kent"
                color: "#888"
                font.pixelSize: 11
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            Label {
                text: "Licensed under MIT License"
                color: "#666"
                font.pixelSize: 10
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
        
        footer: DialogButtonBox {
            Button {
                text: "OK"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            background: Rectangle { color: "#333" }
        }
    }

    // Getting Started Dialog
    Dialog {
        id: gettingStartedDialog
        title: "Getting Started"
        modal: true
        anchors.centerIn: parent
        width: 560
        height: 500

        background: Rectangle { color: "#2a2a2a"; border.color: "#555"; border.width: 1; radius: 8 }
        header: Label { text: gettingStartedDialog.title; color: "white"; font.pixelSize: 16; font.bold: true; padding: 16; background: Rectangle { color: "#333"; radius: 8 } }

        contentItem: Flickable {
            contentHeight: gsCol.implicitHeight + 20
            clip: true
            flickableDirection: Flickable.VerticalFlick
            Basic.ScrollBar.vertical: Basic.ScrollBar { policy: Basic.ScrollBar.AsNeeded }

            Column {
                id: gsCol
                width: parent.width - 20
                x: 10; y: 10
                spacing: 14

                Label { text: "Welcome to Project Nimbus"; color: "#4a9eff"; font.pixelSize: 15; font.bold: true; wrapMode: Text.WordWrap; width: parent.width }
                Label { text: "Project Nimbus transforms mouse, wheelchair joystick, or other pointing device input into virtual game controller commands via vJoy."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "1. Choose a Profile"; color: "#ff8833"; font.pixelSize: 13; font.bold: true }
                Label { text: "Go to File → Profile to select a layout:\n• Flight Simulator — dual joysticks, throttle, rudder\n• Xbox Controller — gamepad-style layout\n• Adaptive Platform — accessibility-focused with large buttons\n• Custom layouts — fully configurable drag-and-drop canvas"; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "2. Custom Layout (Recommended)"; color: "#ff8833"; font.pixelSize: 13; font.bold: true }
                Label { text: "Click Edit Layout in the menu bar to enter edit mode. The Widget Palette appears with:\n• Joystick — 2-axis stick (up to 4 pairs)\n• Button — up to 128 buttons with toggle/momentary modes\n• H/V Slider — single-axis controls (throttle, triggers)\n• D-Pad — 4-directional digital pad\n• Wheel — rotational single-axis\n\nDrag widgets onto the canvas, resize them, and double-click to configure. Click Done Editing when finished."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "3. Wheelchair Joystick Setup"; color: "#ff8833"; font.pixelSize: 13; font.bold: true }
                Label { text: "For wheelchair-mounted joysticks that control the mouse cursor:\n\n1. Add a Joystick widget and double-click to configure\n2. Enable Triple-click lock (on by default)\n3. Enable Auto-return to center when locked\n4. Set Delay to 1-5ms for responsive return\n5. Adjust Lock Sensitivity (higher = more responsive)\n6. Set Tremor Filter if your input is jittery (higher = smoother)\n\nTriple-click the joystick to lock. Your cursor becomes invisible and is anchored to the joystick center. Physical joystick movement translates directly to virtual deflection. Triple-click again to unlock."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "4. Per-Widget Settings"; color: "#ff8833"; font.pixelSize: 13; font.bold: true }
                Label { text: "Double-click any widget to configure:\n• Axis mapping — which vJoy axis to control\n• Sensitivity — response curve (0-100%)\n• Dead zone — ignore small inputs near center\n• Extremity dead zone — snap to full at edges\n• Copy settings from other widgets via dropdown"; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "5. Game Focus Mode"; color: "#ff8833"; font.pixelSize: 13; font.bold: true }
                Label { text: "Enable via View → Game Focus Mode. When active, clicking Project Nimbus won't steal focus from your game — the game window stays in the foreground."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }
            }
        }

        footer: DialogButtonBox {
            Button {
                text: "Close"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            background: Rectangle { color: "#333" }
        }
    }

    // Feature Guide Dialog
    Dialog {
        id: featureGuideDialog
        title: "Feature Guide"
        modal: true
        anchors.centerIn: parent
        width: 560
        height: 500

        background: Rectangle { color: "#2a2a2a"; border.color: "#555"; border.width: 1; radius: 8 }
        header: Label { text: featureGuideDialog.title; color: "white"; font.pixelSize: 16; font.bold: true; padding: 16; background: Rectangle { color: "#333"; radius: 8 } }

        contentItem: Flickable {
            contentHeight: fgCol.implicitHeight + 20
            clip: true
            flickableDirection: Flickable.VerticalFlick
            Basic.ScrollBar.vertical: Basic.ScrollBar { policy: Basic.ScrollBar.AsNeeded }

            Column {
                id: fgCol
                width: parent.width - 20
                x: 10; y: 10
                spacing: 14

                Label { text: "Widget Types"; color: "#4a9eff"; font.pixelSize: 15; font.bold: true; wrapMode: Text.WordWrap; width: parent.width }
                Label { text: "• Joystick — 2-axis control (X/Y, RX/RY, Z/RZ, SL0/SL1). Supports triple-click lock for wheelchair joysticks with auto-return, sensitivity, and tremor filtering.\n• Button — Momentary (hold) or Toggle (click on/off). Up to 128 buttons, customizable color and shape.\n• H Slider / V Slider — Single-axis with snap modes: Hold position, Return to zero, or Spring to center.\n• D-Pad — 4 directional buttons mapped to vJoy button IDs.\n• Steering Wheel — Rotational single-axis control."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "Joystick Lock Mode (FPS-Style Delta Tracking)"; color: "#4a9eff"; font.pixelSize: 15; font.bold: true; wrapMode: Text.WordWrap; width: parent.width }
                Label { text: "When you triple-click a joystick:\n• Cursor becomes invisible and is anchored to joystick center\n• Mouse movements are treated as deflection deltas\n• Cursor is continuously warped back to center (like FPS mouse look)\n• Auto-return snaps joystick to center when you stop moving\n\nThis is designed for wheelchair joysticks where the physical stick controls cursor velocity. The virtual joystick deflection directly mirrors the physical stick position."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "Lock Settings"; color: "#4a9eff"; font.pixelSize: 15; font.bold: true }
                Label { text: "• Lock Sensitivity (1-10) — How responsive the locked joystick is. Higher values require less physical movement for full deflection. Start at 4 and adjust.\n• Tremor Filter (0-10) — Smooths out jittery input. 0 = off, higher = more smoothing. Useful for wheelchair joysticks with tremor.\n• Auto-return Delay (1-10ms) — How quickly the joystick returns to center when you stop moving. Lower = faster snap back."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "Sensitivity & Dead Zones"; color: "#4a9eff"; font.pixelSize: 15; font.bold: true }
                Label { text: "Each axis widget has per-widget settings:\n• Sensitivity (0-100%) — Response curve. 50% = linear, lower = more precision near center, higher = more responsive.\n• Dead Zone (0-100%) — Ignores small inputs near the center position.\n• Extremity Dead Zone (0-100%) — Snaps to full deflection near the edges.\n• Copy From — Copy settings from another axis widget."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "Virtual Controller Output"; color: "#4a9eff"; font.pixelSize: 15; font.bold: true }
                Label { text: "Project Nimbus outputs to:\n• vJoy — 8 axes (4 joystick pairs max), 128 buttons. Must have vJoy driver installed.\n• ViGEm (planned) — Xbox 360 controller emulation with 2 sticks, 2 triggers, 14 buttons."; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }

                Label { text: "Keyboard Shortcuts"; color: "#4a9eff"; font.pixelSize: 15; font.bold: true }
                Label { text: "• Triple-click — Lock/unlock joystick\n• Double-click widget (edit mode) — Open widget config\n• Drag widget edges (edit mode) — Resize"; color: "#ccc"; font.pixelSize: 12; wrapMode: Text.WordWrap; width: parent.width }
            }
        }

        footer: DialogButtonBox {
            Button {
                text: "Close"
                DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole
            }
            background: Rectangle { color: "#333" }
        }
    }

    // Layout loader - switches between Flight Sim, Xbox, Adaptive, and Custom layouts
    Loader {
        id: layoutLoader
        anchors.fill: parent
        sourceComponent: {
            if (root.layoutType === "custom") return customLayout
            if (root.layoutType === "adaptive") return adaptiveLayout
            if (root.layoutType === "xbox") return xboxLayout
            return flightSimLayout
        }
    }

    // Flight Simulator layout component
    Component {
        id: flightSimLayout
        Layouts.FlightSimLayout {
            scaleFactor: root.scaleFactor
        }
    }

    // Xbox Controller layout component
    Component {
        id: xboxLayout
        Layouts.XboxLayout {
            scaleFactor: root.scaleFactor
        }
    }

    // Adaptive Controller layout component (accessibility-focused)
    Component {
        id: adaptiveLayout
        Layouts.AdaptiveLayout {
            scaleFactor: root.scaleFactor
        }
    }

    // Custom modular layout component (drag-and-drop canvas)
    Component {
        id: customLayout
        Layouts.CustomLayout {
            scaleFactor: root.scaleFactor
        }
    }
}
