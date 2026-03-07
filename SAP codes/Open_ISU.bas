Sub Open_ISU()

    Dim SapGuiAuto As Object
    Dim SAPAPP     As Object
    Dim Connection As Object
    Dim SapSession As Object
    Dim oConn      As Object

    ' --- Check if SAP GUI is already running ---
    On Error Resume Next
    Set SapGuiAuto = GetObject("SAPGUI")
    On Error GoTo 0

    ' --- If not running, launch it and wait ---
    If Not IsObject(SapGuiAuto) Then
        Call Shell("C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe", 1)
        Application.Wait Now + TimeSerial(0, 0, 5)

        On Error Resume Next
        Set SapGuiAuto = GetObject("SAPGUI")
        On Error GoTo 0

        If Not IsObject(SapGuiAuto) Then
            MsgBox "SAP GUI failed to launch. Please open it manually.", vbCritical
            Exit Sub
        End If
    End If

    ' --- Get scripting engine ---
    Set SAPAPP = SapGuiAuto.GetScriptingEngine

    ' --- Check if a TXUE ISU connection already exists ---
    For Each oConn In SAPAPP.Children
        If InStr(oConn.Description, "TXUE ISU") > 0 Then
            Set Connection = oConn
            Exit For
        End If
    Next oConn

    ' --- If no existing connection, open one ---
    If Not IsObject(Connection) Then
        Set Connection = SAPAPP.OpenConnection("01)  TXUE ISU Prod", True)
        Application.Wait Now + TimeSerial(0, 0, 2)
    End If

    ' --- If session(s) already exist, open a new one; otherwise use existing ---
    If Connection.Children.Count > 0 Then
        Connection.Children(0).CreateSession
        Application.Wait Now + TimeSerial(0, 0, 2)
        Set SapSession = Connection.Children(Connection.Children.Count - 1)
    Else
        Set SapSession = Connection.Children(0)
    End If

End Sub
