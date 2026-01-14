<template>
  <div class="schema-tree">
    <SchemaTreeNode
      v-for="(value, key) in schema"
      :key="String(key)"
      :field-name="String(key)"
      :field-value="value"
      :depth="0"
      :search="search"
    />
  </div>
</template>

<script setup lang="ts">
import SchemaTreeNode from './SchemaTreeNode.vue';

defineProps<{
  schema: Record<string, any>;
  search?: string;
}>();
</script>

<style scoped lang="scss">
.schema-tree {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
}
</style>
