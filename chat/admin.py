from django.contrib import admin

from .models import Conversation, UserFact, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'assistant_name', 'avatar_emoji', 'n8n_workflow_id']
    search_fields = ['user__username', 'assistant_name']
    list_select_related = ['user']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'turn_count', 'created_at', 'updated_at']
    list_filter = ['user']
    search_fields = ['title', 'user__username']
    list_select_related = ['user']
    readonly_fields = ['turn_count', 'summary']


@admin.register(UserFact)
class UserFactAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'key', 'value', 'created_at']
    list_filter = ['category', 'user']
    search_fields = ['user__username', 'key', 'value']
    list_select_related = ['user']
