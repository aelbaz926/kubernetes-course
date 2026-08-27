{{/*
Generate a full name: <release-name>-<component>
*/}}
{{- define "feedback-app.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels applied to all resources
*/}}
{{- define "feedback-app.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels for a specific component
*/}}
{{- define "feedback-app.selectorLabels" -}}
app: {{ . }}
{{- end -}}
